#!/usr/bin/env python3
"""Export Yahoo Finance quotes to the Aplexd CSV format, using yfinance locally."""
import argparse
import csv
import datetime as dt
import json
import math
import re
import sys
import time
import warnings
from collections import defaultdict
from pathlib import Path

OPTION = re.compile(r"^([A-Z][A-Z0-9.]*)\s+(\d{2})(\d{2})(\d{2})([CP])(\d{8})$")
HEADERS = ["contract", "underlying", "type", "quantity", "option_price_usd", "underlying_price_usd", "iv_percent", "rate_percent", "dividend_percent", "expiry", "option_type", "strike", "quote_timestamp_utc", "underlying_timestamp_utc"]


def num(v):
    try:
        n = float(str(v).replace(',', '.'))
        return n if math.isfinite(n) else None
    except (TypeError, ValueError):
        return None


def positive(v):
    v = num(v)
    return v if v is not None and v > 0 else None


def iso(value):
    if value is None or str(value) in ('NaT', 'nan', ''):
        return ''
    try:
        stamp = value.to_pydatetime() if hasattr(value, 'to_pydatetime') else value
        if isinstance(stamp, dt.date) and not isinstance(stamp, dt.datetime):
            stamp = dt.datetime.combine(stamp, dt.time(), dt.timezone.utc)
        if isinstance(stamp, dt.datetime):
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=dt.timezone.utc)
            return stamp.astimezone(dt.timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
    except (ValueError, TypeError, OverflowError):
        pass
    return ''


def description(contract, qty):
    m = OPTION.match(contract)
    if not m:
        return dict(contract=contract, underlying=contract, type='STOCK', quantity=qty)
    symbol, yy, mm, dd, cp, strike = m.groups()
    expiry = f'20{yy}-{mm}-{dd}'
    return dict(contract=contract, underlying=symbol, type='OPTION', quantity=qty,
                expiry=expiry, option_type=cp, strike=str(int(strike)/1000))


def read_positions(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.reader(f))
    headers = next((r for r in rows if len(r)>1 and r[0]=='Histórico de transações' and r[1]=='Header'), None)
    if headers:
        idx = {k:i for i,k in enumerate(headers)}
        if any(k not in idx for k in ('Símbolo','Quantidade','Tipo de transação')):
            raise ValueError('O CSV IBKR não contém Símbolo, Quantidade e Tipo de transação.')
        positions = defaultdict(float)
        for r in rows:
            if len(r)<=max(idx[k] for k in ('Símbolo','Quantidade','Tipo de transação')) or r[:2]!=['Histórico de transações','Data']:
                continue
            if r[idx['Tipo de transação']] not in ('Compra','Venda','Atribuição'):
                continue
            symbol = r[idx['Símbolo']].strip().upper()
            quantity = num(r[idx['Quantidade']])
            if symbol and quantity is not None:
                positions[symbol] += quantity
        print('Fonte: histórico IBKR (posições inferidas pelas quantidades; confirmar atribuições).')
    else:
        reader = csv.DictReader(path.open(encoding='utf-8-sig', newline=''))
        if not {'contract','quantity'}.issubset(reader.fieldnames or []):
            raise ValueError('Entrada deve ser CSV IBKR ou CSV exportado pelo Aplexd com contract e quantity.')
        positions = {}
        reference_spots = {}
        for r in reader:
            contract = r['contract'].strip().upper()
            q = num(r['quantity'])
            if contract and q is not None:
                positions[contract] = q
                reference_spots[contract] = positive(r.get('underlying_price_usd')) or positive(r.get('option_price_usd')) if contract == (r.get('underlying') or contract) else positive(r.get('underlying_price_usd'))
        print('Fonte: CSV de cotações Aplexd (quantidades já exportadas).')
    today = dt.datetime.now(dt.timezone.utc).date()
    out = []
    for contract, q in positions.items():
        if abs(q)<1e-8:
            continue
        item = description(contract, q)
        if not headers:
            item['reference_spot'] = reference_spots.get(contract)
        if item['type']=='OPTION' and dt.date.fromisoformat(item['expiry']) < today:
            continue
        out.append(item)
    return sorted(out, key=lambda x:(x['underlying'], x['contract']))


class Yahoo:
    def __init__(self, folder, delay, ttl):
        self.folder = folder
        folder.mkdir(parents=True, exist_ok=True)
        self.delay = delay
        self.ttl = ttl
        self.last = 0
        self.requests = 0

    def call(self, key, fetch):
        file = self.folder / (re.sub('[^A-Za-z0-9_.-]', '_', key)+'.json')
        if file.exists() and time.time()-file.stat().st_mtime < self.ttl*3600:
            return json.loads(file.read_text(encoding='utf-8'))
        remaining = self.delay-(time.monotonic()-self.last)
        if remaining>0:
            time.sleep(remaining)
        try:
            value = fetch()
            self.last = time.monotonic()
            self.requests += 1
            file.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
            return value
        except Exception:
            self.last = time.monotonic()
            self.requests += 1
            raise


def stock_quote(t, cache, symbol):
    def get():
        hist = t.history(period='5d', interval='1d', auto_adjust=False)
        if hist is None or hist.empty:
            return {'price': None, 'time': ''}
        close = positive(hist['Close'].iloc[-1])
        return {'price': close, 'time': iso(hist.index[-1])}
    return cache.call('stock_'+symbol, get)


def chain_quote(t, cache, symbol, expiry):
    def get():
        chain = t.option_chain(expiry)
        records = []
        for frame in (chain.calls, chain.puts):
            if frame is None:
                continue
            for row in frame.to_dict('records'):
                records.append({
                    'contract': str(row.get('contractSymbol', '')).replace(' ', '').upper(),
                    'bid': num(row.get('bid')), 'ask': num(row.get('ask')),
                    'last': num(row.get('lastPrice')),
                    'iv': num(row.get('impliedVolatility')),
                    'lastTradeDate': iso(row.get('lastTradeDate')),
                    'currency': str(row.get('currency') or '').upper(),
                })
        return records
    return cache.call('options_'+symbol+'_'+expiry, get)


def price_for(row, max_last_age):
    bid, ask, last = positive(row.get('bid')), positive(row.get('ask')), positive(row.get('last'))
    if bid and ask and ask>=bid:
        return (bid+ask)/2, 'mid bid/ask', ''
    if last:
        timestamp = row.get('lastTradeDate') or ''
        try:
            age = dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(timestamp.replace('Z','+00:00'))
            if dt.timedelta(0)<=age<=dt.timedelta(days=max_last_age):
                return last, 'last trade', timestamp
        except ValueError:
            pass
    return None, 'sem cotação válida', ''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('extrato', type=Path, help='CSV de transações IBKR ou CSV de cotações exportado pelo Aplexd')
    p.add_argument('-o','--output',type=Path,default=Path('aplexd_cotacoes_yahoo.csv'))
    p.add_argument('--delay',type=float,default=3,help='Segundos mínimos entre chamadas a Yahoo (padrão: 3)')
    p.add_argument('--cache-hours',type=float,default=6,help='Validade da cache local, em horas (padrão: 6)')
    p.add_argument('--max-requests',type=int,default=50,help='Máximo de chamadas por execução (padrão: 50)')
    p.add_argument('--max-last-age-days',type=int,default=3,help='Idade máxima de último negócio sem bid/ask (padrão: 3)')
    p.add_argument('--ticker',action='append',default=[],metavar='SYMBOL=YAHOO',help='Mapeamento manual, ex. SGLD=SGLD.L')
    a=p.parse_args()
    if a.delay<0 or a.max_requests<1:
        p.error('--delay deve ser >=0 e --max-requests >=1')
    # yfinance 1.7.0 calls DataFrame.sort_index(inplace=True), deprecated in
    # pandas 3.1. Hide only this known upstream compatibility warning.
    warnings.filterwarnings(
        "ignore",
        message=r"The inplace keyword in DataFrame\\.sort_index is deprecated.*",
        category=Warning,
        module=r"yfinance\\.utils",
    )
    try:
        import yfinance as yf
    except ImportError:
        sys.exit('Falta a dependência: python -m pip install yfinance')
    mapping = {}
    for pair in a.ticker:
        if '=' not in pair:
            p.error('--ticker deve ter forma SYMBOL=YAHOO')
        k,v=pair.split('=',1)
        mapping[k.upper()]=v
    positions=read_positions(a.extrato)
    cache=Yahoo(a.output.parent/'.aplexd_yahoo_cache',a.delay,a.cache_hours)
    symbols=defaultdict(list)
    for pos in positions:
        symbols[pos['underlying']].append(pos)
    results=[]
    matched=0
    for symbol,group in sorted(symbols.items()):
        ticker_symbol=mapping.get(symbol, symbol)
        t=yf.Ticker(ticker_symbol)
        try:
            if cache.requests>=a.max_requests:
                raise RuntimeError('limite de pedidos atingido')
            spot=stock_quote(t,cache,ticker_symbol)
        except Exception as e:
            print(f'[AVISO] {symbol}: ação sem cotação: {type(e).__name__}: {e}',file=sys.stderr)
            spot={'price':None,'time':''}
        chains={}
        for expiry in sorted({p['expiry'] for p in group if p['type']=='OPTION'}):
            try:
                if cache.requests>=a.max_requests:
                    raise RuntimeError('limite de pedidos atingido')
                data=chain_quote(t,cache,ticker_symbol,expiry)
                chains[expiry]={x['contract']:x for x in data}
            except Exception as e:
                print(f'[AVISO] {symbol} {expiry}: sem cadeia: {type(e).__name__}: {e}',file=sys.stderr)
                chains[expiry]={}
        for pos in group:
            out={k:'' for k in HEADERS}
            out.update(pos)
            # Nunca transformar preços GBP/EUR em USD silenciosamente.
            if ticker_symbol.upper().endswith(('.L','.PA','.DE','.MI','.LS')):
                print(f'[AVISO] {symbol}: confirmar moeda Yahoo antes de importar, preço deixado vazio.',file=sys.stderr)
            else:
                reference=positive(pos.get('reference_spot'))
                candidate=positive(spot['price'])
                if reference and candidate and not 0.5<=candidate/reference<=2:
                    print(f'[ALERTA] {symbol}: Yahoo {candidate:.3f} versus CSV {reference:.3f} (>50%): possível ticker de instrumento diferente. Preço NÃO exportado. Usa --ticker ou verifica a bolsa.', file=sys.stderr)
                    candidate=None
                out['underlying_price_usd']=candidate or ''
                out['underlying_timestamp_utc']=spot['time']
            if pos['type']=='OPTION':
                occ=pos['contract'].replace(' ','').upper()
                quote=chains.get(pos['expiry'],{}).get(occ)
                if quote and quote['currency'] in ('','USD'):
                    value,method,timestamp=price_for(quote,a.max_last_age_days)
                    out['option_price_usd']=value or ''
                    out['quote_timestamp_utc']=timestamp  # Yahoo does not date-stamp bid/ask quotes
                    iv=num(quote['iv'])
                    if iv is not None and 0.001<iv<10:
                        out['iv_percent']=round(iv*100,4)
                    if value is not None:
                        matched+=1
                    print(f'{occ}: {method}; IV={out["iv_percent"] or "indisponível"}')
                else:
                    print(f'[AVISO] {occ}: contrato ausente ou moeda diferente de USD',file=sys.stderr)
            elif not ticker_symbol.upper().endswith(('.L','.PA','.DE','.MI','.LS')):
                out['option_price_usd']=candidate or ''
                out['quote_timestamp_utc']=spot['time']
            results.append({key: out.get(key, '') for key in HEADERS})
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(results)
    print(f'\nCSV: {a.output} | {len(results)} posições | {matched} opções com preço | {cache.requests} chamadas de rede')
    print('IMPORTANTE: no Aplexd, escolher Cancelar no diálogo para preservar cotações existentes e preencher só valores disponíveis.')


if __name__=='__main__':
    main()