import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, html, dcc
from slownik import Diki
import pandas as pd

diki = Diki()

app = dash.Dash(
    external_stylesheets=[dbc.themes.DARKLY]
)

app.layout = dbc.Container(
    [
        dcc.Store(
            id='translation'
        ),
        dbc.InputGroup(
            [
                dbc.InputGroupText(
                    "🇬🇧", 
                    className="text-white bg-dark"
                ), 
                dbc.Input(
                    id='input_word',
                    placeholder="English word", 
                    className="bg-dark text-white"
                )
            ],
            className="mb-3",
        ),
        dbc.Checklist(
            id='checklist_polish_words',
            # switch=True,
            inputClassName="bg-dark",
            labelClassName="text-white"

        ),
        html.Div(id='test_output')
    ],
    className="p-5 text-white",
    style={
        "color":"white"
    }
)

@app.callback(
    [Output('translation', 'data'),
    Output('checklist_polish_words','options'),
    Output('checklist_polish_words','value')],
    Input('input_word', 'value')
)
def writing_word(input_value):

    diki.extract_data(input_value)

    return [
        diki.data.to_dict('records'),
        [{'label': row.polish_word, 'value': i} for i, row in diki.data.iterrows()],
        []
    ]

@app.callback(
    Output('test_output', 'children'),
    Input('checklist_polish_words', 'value'),
    State('translation', 'data')
)
def update_checkboxes(selected_value, data):
    if data is None or not data:
        return "Brak danych."

    df = pd.DataFrame(data)

    if not selected_value:
        return "Nic nie zaznaczono."

    selected_df = df.iloc[selected_value]

    print(selected_df['pronunciation'])

    return None


if __name__ == "__main__":
    app.run_server(debug=True)
