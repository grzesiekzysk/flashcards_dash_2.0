import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, html, dcc
from slownik import Diki
import pandas as pd

# Słownik z użytkownikami i ich PIN-ami
USER_DATA = {
    'Karolina': '1234',
    'Grzesiek': '5678'
}

# Inicjalizacja klasy Diki
diki = Diki()

app = dash.Dash(
    external_stylesheets=[dbc.themes.DARKLY]
)

app.layout = dbc.Container(
    [
        # Przechowywanie stanu zalogowania
        dcc.Store(id='login-status', data={'logged_in': False, 'user': None}),
        dcc.Store(id='translation'),
        
        # Sekcja wyszukiwania słów
        html.Div(
            [
                dbc.InputGroup(
                    [
                        dbc.InputGroupText('🇬🇧', className='text-white bg-dark'),
                        dbc.Input(
                            id='input_word',
                            placeholder='English word',
                            className='bg-dark text-white'
                        )
                    ],
                    className='mb-3',
                ),
                dbc.Checklist(
                    id='checklist_polish_words',
                    inputClassName='bg-dark',
                    labelClassName='text-white',
                    style={
                        'margin-top': '10px',
                        'margin-bottom': '10px'
                    }
                ),
                dbc.ButtonGroup(
                    id='flashcards_buttons',
                    children=[
                        dbc.Button('Dodaj', color='success', id='add-button'),
                        dbc.Button('Wyślij do bazy', color='danger', id='send-button')
                    ],
                    style={'display': 'none'} 
                )
            ],
            id='search-section',
            className='mb-5'
        ),
        
        # Sekcja logowania
        html.Div(
            id='login-section',
            children=[
                html.Div(
                    id='login-form',
                    children=[
                        dbc.InputGroup(
                            [
                                dbc.Select(
                                    id='shorthand-select',
                                    options=[
                                        {'label': 'Karolina', 'value': 'Karolina'},
                                        {'label': 'Grzesiek', 'value': 'Grzesiek'}
                                    ],
                                    placeholder='User',
                                    value='Karolina',
                                    style={'max-width': '150px'}
                                ),
                                dbc.Input(
                                    id='input_pin',
                                    type='password',
                                    inputmode='numeric',
                                    placeholder='PIN',
                                    maxLength=4,
                                    className='bg-dark text-white',
                                    style={
                                        'max-width': '80px', 
                                        'text-align': 'center'
                                    }
                                ),
                                dbc.Button(
                                    'Zaloguj',
                                    id='login-button',
                                    color='warning'
                                )
                            ],
                            className='mt-3'
                        )
                    ],
                    className='mb-3'
                ),
                html.Div(
                    id='logged-in-user',
                    children='',
                    className='mt-3 text-white'
                ),
                dbc.Button(
                    'Wyloguj',
                    id='logout-button',
                    color='danger',
                    className='mt-3',
                    style={'display': 'none'}  # Ukryty, gdy użytkownik jest niezalogowany
                )
            ],
            className='mt-5'
        )
    ],
    className='p-5 text-white',
    style={'color': 'white'}
)

# Callback do wyszukiwania słów
@app.callback(
    [
        Output('translation', 'data'),
        Output('checklist_polish_words', 'options'),
        Output('checklist_polish_words', 'value')
    ],
    Input('input_word', 'value'),
    prevent_initial_call=True
)
def search_word(input_value):
    if not input_value:
        raise dash.exceptions.PreventUpdate

    diki.extract_data(input_value)
    return [
        diki.data.to_dict('records'),
        [{'label': row.polish_word, 'value': i} for i, row in diki.data.iterrows()],
        []
    ]

# Callback do logowania i wylogowania
@app.callback(
    [
        Output('login-status', 'data'),
        Output('login-form', 'style'),
        Output('logout-button', 'style'),
        Output('logged-in-user', 'children'),
        Output('flashcards_buttons','style')
    ],
    [Input('login-button', 'n_clicks'),
     Input('logout-button', 'n_clicks')],
    [State('shorthand-select', 'value'),
     State('input_pin', 'value'),
     State('login-status', 'data')],
    prevent_initial_call=True
)
def handle_login_logout(login_clicks, logout_clicks, username, pin, login_status):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'login-button':
        if username in USER_DATA and USER_DATA[username] == pin:
            return (
                {'logged_in': True, 'user': username},
                {'display': 'none'},  # Ukryj formularz logowania
                {'display': 'block'},  # Pokaż przycisk Wyloguj
                f'Zalogowano jako: {username}',
                {'display': 'block'}
            )
        return login_status, {}, {'display': 'none'}, 'Niepoprawny użytkownik lub PIN.'

    elif triggered_id == 'logout-button':
        return (
            {'logged_in': False, 'user': None},
            {},  # Pokaż formularz logowania
            {'display': 'none'},  # Ukryj przycisk Wyloguj
            '',  # Usuń informację o zalogowanym użytkowniku
            {'display': 'none'}
        )

if __name__ == '__main__':
    app.run_server(debug=True)
    # app.run_server(debug=True, host='0.0.0.0')