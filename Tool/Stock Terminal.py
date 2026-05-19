import akshare as ak
import pandas as pd
import plotly.graph_objects as go
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from datetime import datetime

# --- 配置持仓 ---
PORTFOLIO = {
    "AAPL": {"shares": 1, "buy_price": 268, "color": "#00f2ff", "name": "Apple Inc."},
    "MSFT": {"shares": 1, "buy_price": 407, "color": "#7000ff", "name": "Microsoft"}
}
TOTAL_COST_USD = sum(v["shares"] * v["buy_price"] for v in PORTFOLIO.values())

app = dash.Dash(__name__)

# --- 注入高级 CSS 动画 ---
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Quantum Terminal</title>
        {%favicon%}
        {%css%}
        <style>
            @keyframes scan {
                0% { transform: translateX(-100%); }
                100% { transform: translateX(100%); }
            }
            .glow-card {
                transition: all 0.5s ease;
                border: 1px solid #222;
            }
            .glow-card:hover {
                border-color: #00f2ff;
                box-shadow: 0 0 15px rgba(0, 242, 255, 0.2);
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# --- UI 布局 ---
app.layout = html.Div(style={
    'backgroundColor': '#020205', 
    'color': '#fff', 'height': '100vh', 'margin': '0', 'overflow': 'hidden',
    'font-family': 'monospace'
}, children=[
    # 顶部扫描灯
    html.Div(style={
        'height': '2px', 
        'width': '100%', 
        'background': 'linear-gradient(90deg, transparent, #00f2ff, transparent)',
        'animation': 'scan 3s linear infinite'
    }),
    
    # 状态头部
    html.Div([
        html.Div([
            html.H2("TERMINAL // QUANTUM_PRO_v4", style={'margin': '0', 'fontSize': '16px', 'letterSpacing': '4px', 'color': '#00f2ff'}),
            html.P(id='live-clock', style={'margin': '0', 'fontSize': '10px', 'opacity': '0.4'})
        ], style={'flex': '1'}),
        html.Div(id='fx-ticker', style={'textAlign': 'right', 'fontSize': '11px', 'color': '#00ff41', 'letterSpacing': '1px'})
    ], style={'padding': '15px 40px', 'background': 'rgba(0,0,0,0.5)', 'borderBottom': '1px solid #111'}),

    html.Div([
        # 左侧：核心数据流
        html.Div([
            # 主盈亏卡片
            html.Div([
                html.P("CUMULATIVE P/L (USD)", style={'fontSize': '10px', 'color': '#888', 'marginBottom': '10px'}),
                html.H1(id='main-pl-display', style={'margin': '0', 'fontSize': '56px', 'fontWeight': 'bold'})
            ], className='glow-card', style={'padding': '30px', 'marginBottom': '20px', 'background': '#050508'}),
            
            # 汇率换算
            html.Div([
                html.Div([
                    html.P("CNY EVAL", style={'fontSize': '9px', 'color': '#f0b90b'}),
                    html.H3(id='cny-pl', style={'margin': '0'})
                ], className='glow-card', style={'flex': '1', 'padding': '20px', 'marginRight': '10px'}),
                html.Div([
                    html.P("JPY EVAL", style={'fontSize': '9px', 'color': '#ff00ff'}),
                    html.H3(id='jpy-pl', style={'margin': '0'})
                ], className='glow-card', style={'flex': '1', 'padding': '20px'})
            ], style={'display': 'flex', 'marginBottom': '20px'}),
            
            # 资产占比图 (Mini Pie)
            dcc.Graph(id='asset-pie', style={'height': '200px'}, config={'displayModeBar': False})
        ], style={'width': '30%', 'padding': '40px', 'borderRight': '1px solid #111'}),

        # 右侧：全屏趋势图
        html.Div([
            dcc.Graph(id='live-trend-graph', style={'height': '80vh'}, config={'displayModeBar': False})
        ], style={'width': '70%', 'padding': '20px'})
    ], style={'display': 'flex'}),

    dcc.Interval(id='refresh-trigger', interval=15*1000, n_intervals=0)
])

# --- 逻辑引擎 ---
def fetch_data():
    raw_data = {}
    current_prices = {}
    for s in PORTFOLIO.keys():
        df = ak.stock_us_daily(symbol=s, adjust="qfq")
        prices = df.set_index(pd.to_datetime(df["date"]))["close"]
        raw_data[s] = prices
        current_prices[s] = prices.iloc[-1]
    
    # 汇率获取
    try:
        fx = ak.fx_spot_quote()
        cny = float(fx[fx['code'] == 'USDCNY']['spot_buy'].iloc[0])
        jpy = float(fx[fx['code'] == 'USDJPY']['spot_buy'].iloc[0])
    except:
        cny, jpy = 7.24, 155.8
        
    pl_series = (pd.DataFrame(raw_data).sum(axis=1) - TOTAL_COST_USD).tail(90)
    return pl_series, cny, jpy, current_prices

@app.callback(
    [Output('main-pl-display', 'children'),
     Output('main-pl-display', 'style'),
     Output('cny-pl', 'children'),
     Output('jpy-pl', 'children'),
     Output('live-trend-graph', 'figure'),
     Output('asset-pie', 'figure'),
     Output('fx-ticker', 'children'),
     Output('live-clock', 'children')],
    [Input('refresh-trigger', 'n_intervals')]
)
def update_all(n):
    try:
        pl_series, cny_r, jpy_r, cur_prices = fetch_data()
        cur_pl_usd = pl_series.iloc[-1]
        color = "#00ff41" if cur_pl_usd >= 0 else "#ff3131"
        
        # 1. 主趋势图
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=pl_series.index, y=pl_series.values,
            mode='lines', line=dict(color=color, width=4, shape='spline'),
            fill='tozeroy', fillcolor=f'rgba({ "0,255,65" if cur_pl_usd >= 0 else "255,49,49" }, 0.03)'
        ))
        fig_trend.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=50, r=50, t=20, b=50),
            xaxis=dict(gridcolor='#111', zeroline=False),
            yaxis=dict(gridcolor='#111', zeroline=False, side='right')
        )

        # 2. 占比饼图
        values = [cur_prices[s] * PORTFOLIO[s]["shares"] for s in PORTFOLIO.keys()]
        fig_pie = go.Figure(data=[go.Pie(
            labels=list(PORTFOLIO.keys()), values=values,
            hole=.7, marker=dict(colors=[PORTFOLIO[s]["color"] for s in PORTFOLIO.keys()]),
            textinfo='none'
        )])
        fig_pie.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=0, b=0), showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        # 3. 动态样式
        usd_style = {'margin': '0', 'fontSize': '56px', 'fontWeight': 'bold', 'color': color, 'textShadow': f'0 0 20px {color}66'}
        
        return (
            f"${cur_pl_usd:+.2f}", usd_style,
            f"¥ {cur_pl_usd * cny_r:,.2f}", f"¥ {cur_pl_usd * jpy_r:,.0f}",
            fig_trend, fig_pie,
            f"USD/CNY {cny_r:.4f}  |  USD/JPY {jpy_r:.2f}",
            f"SYNC_OK // {datetime.now().strftime('%H:%M:%S')}"
        )
    except Exception as e:
        return "SYNC_ERR", {}, "---", "---", go.Figure(), go.Figure(), str(e), "RECONNECTING..."

if __name__ == '__main__':
    app.run(debug=False, port=8050)