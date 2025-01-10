import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, html, dcc
from slownik import Diki
# from connections import mysql
import pandas as pd
import pymysql
from io import StringIO

def mysql():
    return pymysql.connect(
        host='34.118.51.170',
        user='app',
        password='Aldehyd09)(',
        database='flashcards'
    )

def check_rows(user):

    try:
        con = mysql()
        c = con.cursor()

        sql_select = """
        SELECT COUNT(*)
        FROM flashcards.flashcards
        WHERE anki = 0
        AND user = %s
        """
        c.execute(sql_select, (user,))
        rows = c.fetchone()

        return rows[0] if rows else 0
    
    except:
        return 0
    
    finally:
        if c:
            c.close()
        if con:
            con.close()

try:
    con = mysql()
    sql_select = "SELECT user, pin FROM users"
    c = con.cursor()
    c.execute(sql_select)
    rows = c.fetchall()
    USER_DATA = {row[0]: row[1] for row in rows}

except Exception as e:
    print(f'Wystąpił błąd: {e}')

finally:
    con.close()

diki = Diki()

app = dash.Dash(
    title='Angielskie fiszki',
    external_stylesheets=[dbc.themes.DARKLY]
)

app.layout = dbc.Container(
    [
        dcc.Store(id='login-status', data={'logged_in': False, 'user': None}),
        dcc.Store(id='translation'),
        dcc.Download(id='download-file'),

        html.Div(
            [
                html.Div(
                    id='login-section',
                    children=[
                        html.Div(
                            id='logged-in-user',
                            children='',
                            className='text-white',
                            style={
                                'text-align': 'right',
                                'margin-right': '20px',
                                'white-space': 'nowrap'
                            }
                        ),
                        dbc.InputGroup(
                            id='login-form',
                            children=[
                                # dbc.Select(
                                #     id='shorthand-select',
                                #     options=[{'label': user, 'value': user} for user in USER_DATA.keys()],
                                #     placeholder='User',
                                #     value='Karolina',
                                #     style={'width': '100px'}
                                # ),
                                dbc.Input(
                                    id='shorthand-select',
                                    placeholder='Login',
                                    style={
                                        'width': '100px',
                                        'text-align': 'center'
                                    }
                                ),
                                dbc.Input(
                                    id='input_pin',
                                    type='password',
                                    inputmode='numeric',
                                    placeholder='PIN',
                                    maxLength=4,
                                    className='bg-dark text-white',
                                    style={
                                        'width': '80px',
                                        'text-align': 'center'
                                    }
                                ),
                                dbc.Button(
                                    'Zaloguj',
                                    id='login-button',
                                    color='warning'
                                )
                            ]
                        ),
                        dbc.ButtonGroup(
                            id='logout-buttons',
                            children=[
                                dbc.Button(
                                    children=[
                                        'Pobierz',
                                        dbc.Badge(
                                            children='0', 
                                            id='n-rows', 
                                            color='danger', 
                                            text_color='black', 
                                            className="ms-1"
                                            )
                                        ], 
                                    color='light', 
                                    id='download', 
                                    outline=True, 
                                    disabled=True
                                ),
                                dbc.Button('Wyloguj',id='logout-button', color='danger')
                            ],
                            style={'display': 'none'}
                        )
                        
                    ],
                    style={
                        'display': 'flex',
                        'flex-direction': 'row',
                        'align-items': 'center',
                        'padding-left': '5px',
                        # 'background-color': 'red'
                    }
                )
            ],
            style={
                'display': 'flex',
                'justify-content': 'right',
                'align-items': 'center',
                'height': '50px',
                'margin-bottom': '10px',
                'margin-top': '10px',
                'width': '100%'
            }
        ),

        html.Div(
            [
                dbc.InputGroup(
                    [
                        dbc.InputGroupText('🇬🇧', className='text-white bg-dark'),
                        dbc.Input(
                            id='input-word',
                            placeholder='English word',
                            className='bg-dark text-white'
                        ),
                        dbc.InputGroupText(id='popularity', className='text-white bg-dark')
                    ],
                    className='mb-3',
                ),
                dbc.ButtonGroup(
                    [
                        dbc.Button('Zaznacz wszystko', color='warning', id='select-all-button', outline=True),
                        dbc.Button('Odznacz wszystko', color='warning', id='deselect-all-button', outline=True),
                        dbc.Button('Dodaj fiszki', color='success', id='send-button', outline=True, disabled=True)
                    ],
                    style={
                        'display': 'inline-block',
                        'text-align': 'center',
                        'margin': '0 auto'
                    },
                    className="d-flex justify-content-center"
                ),
                dbc.Checklist(
                    id='checklist-polish-words',
                    inputClassName='bg-dark',
                    labelClassName='text-white',
                    style={
                        'margin-top': '10px',
                        'margin-bottom': '10px'
                    }
                )
            ],
            id='search-section',
            className='mb-5',
        ),

        html.Div(id='output-1-div', className='mt-3 text-white'),
        html.Div(id='output-2-div', className='mt-3 text-white')

    ],
    className='text-white',
)

@app.callback(
    [
        Output('translation','data', allow_duplicate=True),
        Output('checklist-polish-words', 'options', allow_duplicate=True),
        Output('checklist-polish-words', 'value', allow_duplicate=True),
        Output('popularity','children')
    ],
    Input('input-word', 'value'),
    prevent_initial_call=True
)
def search_word(input_value):
    if not input_value:
        raise dash.exceptions.PreventUpdate
    
    dict_pos = {
        'rzeczownik': 'danger',
        'czasownik': 'success',
        'przymiotnik': 'warning',
        'przysłówek': 'info'
    }

    diki.extract_data(input_value)
    return [
        diki.data.to_dict('records'),
        [
            {
                'label': [
                    row.polish_word,
                    dbc.Badge(
                        row.part_of_speech, 
                        color=dict_pos[row.part_of_speech] if row.part_of_speech in dict_pos else 'primary', 
                        className="me-1",
                        pill=True,
                        style={
                            'margin-left': '5px'
                        }
                    ),
                    (
                    dbc.Badge(
                        '✍️', 
                        color='secondary', 
                        className="me-1",
                        pill=True
                    )
                    if row.pol_example is not None
                    else None)
                    ],
                    
                'value': i
            } 
        for i, row in diki.data.iterrows()],
        [],
        diki.popularity
    ]

@app.callback(
    [
        Output('login-status', 'data'),
        Output('login-form', 'style'),
        Output('logout-buttons', 'style'),
        Output('logged-in-user', 'children'),
        Output('send-button','disabled'),
        Output('n-rows','children', allow_duplicate=True)
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
                {'display': 'none'},
                {'display': 'block'},
                f'Zalogowano jako: {username}',
                False,
                check_rows(username)
            )
        return (
            login_status, 
            {}, 
            {'display': 'none'},
            'Niepoprawny PIN',
            True,
            check_rows(username)
        )

    elif triggered_id == 'logout-button':
        return (
            {'logged_in': False, 'user': None},
            {},
            {'display': 'none'},
            '',
            True,
            check_rows(username)
        )
    
@app.callback(
    Output('output-1-div', 'children'),
    Input('checklist-polish-words', 'value'),
    State('translation', 'data'),
    prevent_initial_call=True
)
def show_clicked_checkbox(selected_values, translation_data):
    if not selected_values or not translation_data:
        return None

    translation_df = pd.DataFrame.from_dict(translation_data)

    try:
        selected_flashcards = translation_df.iloc[selected_values]
    except IndexError:
        return "Błąd: Wybrane wartości nie istnieją w danych."

    flashcards_layout = []

    for _, row in selected_flashcards.iterrows():

        front_content = [row['polish_word']]
        if row['pol_example']:
            front_content.extend([html.Br(), html.Br(), row['pol_example']])

        back_content = [row['english_word'], html.Br(), row['pronunciation']]
        if row['eng_example']:
            back_content.extend([html.Br(), html.Br(), row['eng_example']])

        flashcards_layout.append(
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    html.P(
                                        children=front_content,  # Dynamicznie generowane dzieci
                                        className="card-text text-center"
                                    )
                                ),
                            ],
                            className="mb-2 h-100",
                            color="warning",
                            outline=True
                        ),
                        width=6
                    ),
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    html.P(
                                        children=back_content,
                                        className="card-text text-center"
                                    )
                                ),
                            ],
                            className="mb-2 h-100",
                            color="warning",
                            outline=True
                        ),
                        width=6
                    )
                ],
                className="g-3 mb-3"
            )
        )

    return flashcards_layout

@app.callback(
    Output('checklist-polish-words', "value", allow_duplicate=True),
    Input('select-all-button', 'n_clicks'),
    State('checklist-polish-words', 'options'),
    prevent_initial_call=True
)
def select_all(n_clicks, options):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    return [option["value"] for option in options]

@app.callback(
    Output('checklist-polish-words', "value", allow_duplicate=True),
    Input('deselect-all-button', 'n_clicks'),
    prevent_initial_call=True
)
def deselect_all(n_clicks):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    
    return []

@app.callback(
    [Output('input-word', 'value'),
    Output('translation','data', allow_duplicate=True),
    Output('checklist-polish-words', 'options', allow_duplicate=True),
    Output('checklist-polish-words', 'value', allow_duplicate=True),
    Output('popularity','children', allow_duplicate=True),
    Output('n-rows','children', allow_duplicate=True)],
    Input('send-button', 'n_clicks'),
    [State('translation', 'data'),
    State('checklist-polish-words', 'value'),
    State('login-status', 'data')],
    prevent_initial_call=True
)
def send_data(n_clicks, translation_data, selected_values, login_status):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    
    translation_df = pd.DataFrame.from_dict(translation_data)

    try:
        selected_flashcards = translation_df.iloc[selected_values]
    except IndexError:
        return '', {}, [], [], ''
    
    columns = ['user', 'front', 'back']

    selected_flashcards = (
        selected_flashcards
        .assign(
            user=login_status['user'],
            front=lambda _df: _df['polish_word'] + _df['pol_example'].apply(
                lambda x: '<br><br>' + '<small>' + x + '</small>' if pd.notna(x) and x != '' else ''
            ),
            back=lambda _df: _df['english_word'] + '<br>' + _df['pronunciation'] + _df['eng_example'].apply(
                lambda x: '<br><br>' + '<small>' + x + '</small>' if pd.notna(x) and x != '' else ''
            )
        )
        .loc[:, columns]
    )

    sql_insert = """
    INSERT INTO flashcards.flashcards
    (user, front_side, back_side)
    VALUES (%s, %s, %s)
    """

    list_of_values = [tuple(None if pd.isna(col) else col for col in row) 
        for row in [i for i in selected_flashcards.itertuples(index=False, name=None)]]
    
    con = mysql()
    c = con.cursor()
    c.executemany(sql_insert, list_of_values)
    con.commit()
    con.close()

    return '', {}, [], [], '', check_rows(login_status['user'])

@app.callback(
    Output('download', 'disabled'),
    Input('n-rows', 'children')
)
def active_download(n_rows):
    try:
        n_rows = int(n_rows)
    except (ValueError, TypeError):
        return True

    return n_rows <= 0
    
@app.callback(
    [Output('n-rows', 'children', allow_duplicate=True),
     Output('download-file', 'data')],
    Input('download', 'n_clicks'),
    State('login-status', 'data'),
    prevent_initial_call=True
)
def download_and_update_rows(n_clicks, login_status):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    user = login_status['user']

    try:
        con = mysql()
        sql_select = """
        SELECT front_side, back_side
        FROM flashcards.flashcards
        WHERE anki = 0
        AND user = %s
        """
        df = pd.read_sql(sql_select, con, params=(user,))

        sql_update = """
        UPDATE flashcards.flashcards
        SET anki = 1
        WHERE anki = 0
        AND user = %s
        """
        with con.cursor() as c:
            c.execute(sql_update, (user,))
        con.commit()
        remaining_rows = check_rows(user)

        return remaining_rows, dcc.send_data_frame(
            df.to_csv,
            "flashcards.txt",
            index=False,
            header=False,
            sep=';'
        )

    except Exception as e:
        print(f"Błąd w funkcji download: {e}")
        raise dash.exceptions.PreventUpdate

    finally:
        con.close()

if __name__ == '__main__':
    # app.run_server(debug=True)
    app.run_server(host='0.0.0.0', port=8080)