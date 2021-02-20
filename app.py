import flask
from flask import request, jsonify
import pandas as pd
import numpy as np
import json

app = flask.Flask(__name__)
app.config["DEBUG"] = True

nasdaq_100_returns = pd.read_csv('data/nasdaq_100_returns.csv', parse_dates=True, index_col='date')
predictions = pd.read_csv('data/predictions.csv', parse_dates=True, index_col=0).T
dates_to_predict = nasdaq_100_returns.iloc[-10::-10].index

def built_comp_list(predictions, n=1):
    cmp_dict = {}
    for dt in predictions.columns:
        dt_serie = predictions[dt].sort_values(ascending=False)
        dt_serie_non_zero = dt_serie[dt_serie != 0]
        comp_list = list(dt_serie_non_zero.head(n).index)
        cmp_dict[dt.strftime('%Y-%m-%d')] = comp_list
    return cmp_dict

def bckt_time_window(dt, bck_test_df, comp_list):
    comp_series = {}
    for comp in bck_test_df.columns:
        if comp in comp_list:
            comp_series[comp] = bck_test_df[comp][dt:].head(10).sort_index(ascending=False)
        else:
            comp_series[comp] = pd.Series(index=bck_test_df[dt:].head(10).index, data = np.nan)
    return pd.DataFrame(comp_series)




@app.route('/', methods=['GET'])
def home():
    return f'''
    <h1>MLChartist</h1>
    <p>The best stock prediction algorithm in the world!</p>
    '''


@app.route('/api/live-backtest', methods=['GET'])
def api_live_backtest():
    # Check if an ID was provided as part of the URL.
    # If ID is provided, assign it to a variable.
    # If no ID is provided, display an error in the browser.
    if 'companies' in request.args:
        N = int(request.args['companies'])
    else:
        return "Error: No number of companies field provided. Please specify an id."

    top_n = built_comp_list(predictions, n=N)

    window_list = []
    for dt, comp_list in top_n.items():
        window_list.append(bckt_time_window(dt, nasdaq_100_returns, comp_list))

    avg_ret = pd.DataFrame(pd.concat(window_list).mean(axis = 1).sort_index(), columns=['avg_return'])

    returns = avg_ret.merge(nasdaq_100_returns['NDX'], left_index=True, right_index=True, how='inner') +1
    final_ret = returns.fillna(value=1)

    response =  {
        'date': final_ret.index.values.tolist(),
        'avg_return': final_ret.avg_return.values.tolist(),
        'NDX': final_ret.NDX.values.tolist()
    }

    return jsonify(response)


@app.route('/api/backtest', methods=['GET'])
def api_cached_backtest():
    # Check if an ID was provided as part of the URL.
    # If ID is provided, assign it to a variable.
    # If no ID is provided, display an error in the browser.
    if 'companies' in request.args:
        N = int(request.args['companies'])
    else:
        return "Error: No number of companies field provided. Please specify an id."

    ## load in json based on companies number
    filename = f'cache/N{N}.txt'
    with open(filename) as json_file:
        response = json.load(json_file)

    ## output it
    return jsonify(response)

app.run()