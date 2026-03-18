from fastapi import FastAPI, HTTPException, Request
import ccxt
import os
import uvicorn

app = FastAPI()

# 1. 初始化交易所 (使用 CCXT)
exchange = ccxt.binance({
    'apiKey': os.getenv('BINANCE_API_KEY'),
    'secret': os.getenv('BINANCE_API_SECRET'),
    'enableRateLimit': True,
    # 如果是跑合约，取消下面这行的注释
    # 'options': {'defaultType': 'future'} 
})

PASSPHRASE = os.getenv('WEBHOOK_PASSPHRASE')

@app.get("/")
def root():
    return {"status": "online"}

@app.post("/webhook")
async def tradingview_webhook(request: Request):
    # 解析 JSON 数据
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # 安全验证
    if data.get('passphrase') != PASSPHRASE:
        raise HTTPException(status_code=401, detail="Unauthorized")

    symbol = data.get('ticker', 'BTC/USDT').replace('USDT', '/USDT') # 转换格式为 BTC/USDT
    side = data.get('action').lower() # 'buy' 或 'sell'
    amount = float(data.get('quantity'))

    try:
        print(f"🚀 执行订单: {symbol} | 方向: {side} | 数量: {amount}")
        
        # 使用 CCXT 执行市价单
        if side == 'buy':
            order = exchange.create_market_buy_order(symbol, amount)
        else:
            order = exchange.create_market_sell_order(symbol, amount)
            
        return {"status": "success", "order_id": order['id']}

    except Exception as e:
        print(f"❌ 下单失败: {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)