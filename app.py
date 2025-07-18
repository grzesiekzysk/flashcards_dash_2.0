"""
Dash app "Angielskie fiszki" – uproszczona wersja (v2.1, kompletna)
===================================================================
• Brak logowania / bazy – tylko pamięć przeglądarki + eksport .txt.
• Fiszki wybierasz, dodajesz do listy, a potem jednym kliknięciem pobierasz.
"""

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, ALL
import pandas as pd
import json

from slownik import Diki

diki = Diki()

app = dash.Dash(
    title="Angielskie fiszki",
    external_stylesheets=[dbc.themes.DARKLY],
)

# -------------------- Layout -------------------------------------------------
app.layout = dbc.Container(
    [
        # wewnętrzne „magazyny”
        dcc.Store(id="translation"),
        dcc.Store(id="saved-flashcards", data=[]),
        dcc.Download(id="download-file"),

        # sekcja wyszukiwania
        html.Div(
            [
                dbc.InputGroup(
                    [
                        dbc.InputGroupText("🇬🇧", className="text-white bg-dark"),
                        dbc.Input(id="input-word", placeholder="English word", className="bg-dark text-white"),
                        dbc.InputGroupText(id="popularity", className="text-white bg-dark"),
                    ],
                    className="mb-3",
                ),
                dbc.ButtonGroup(
                    [
                        dbc.Button("Zaznacz wszystko", id="select-all-button", color="warning", outline=True),
                        dbc.Button("Odznacz wszystko", id="deselect-all-button", color="warning", outline=True),
                        dbc.Button("Dodaj fiszki", id="send-button", color="success", outline=True, disabled=True),
                    ],
                    className="d-flex justify-content-center",
                ),
                dbc.Checklist(
                    id="checklist-polish-words",
                    inputClassName="bg-dark",
                    labelClassName="text-white",
                    style={"marginTop": "10px", "marginBottom": "10px"},
                ),
            ],
        ),

        # podglądy
        html.Div(id="output-2-div", className="mt-3 text-white"),  # inne tłumaczenia
        html.Div(id="output-1-div", className="mt-3 text-white"),  # wybrane fiszki

        html.Hr(),

        # pobieranie
        dbc.Button(
            [
                "Pobierz wszystkie ",
                dbc.Badge("0", id="n-rows", color="danger", text_color="black", className="ms-1"),
            ],
            id="download",
            color="light",
            outline=True,
            disabled=True,
            className="mb-5",
        ),
    ],
    className="text-white",
)

# -------------------- Callbacks ---------------------------------------------

# 1️⃣ pobieranie danych z Diki --------------------------------------------------
@app.callback(
    [
        Output("translation", "data", allow_duplicate=True),
        Output("checklist-polish-words", "options", allow_duplicate=True),
        Output("checklist-polish-words", "value", allow_duplicate=True),
        Output("popularity", "children"),
        Output("output-2-div", "children"),
    ],
    Input("input-word", "value"),
    prevent_initial_call=True,
)
def search_word(word):
    if not word:
        raise dash.exceptions.PreventUpdate

    diki.extract_data(word)
    part_cols = {"rzeczownik": "danger", "czasownik": "success", "przymiotnik": "warning", "przysłówek": "info"}

    options = [
        {
            "label": [
                row.polish_word,
                dbc.Badge(row.part_of_speech, color=part_cols.get(row.part_of_speech, "primary"), className="me-1", pill=True, style={"marginLeft": "5px"}),
                dbc.Badge("✍️", color="secondary", className="me-1", pill=True) if pd.notna(row.pol_example) else None,
            ],
            "value": i,
        }
        for i, row in diki.data.iterrows()
    ]

    badges = [
        dbc.Badge(word, id={"type": "otherword-badge", "index": i}, color="light", className="me-1 text-decoration-none", text_color="dark", style={"cursor": "pointer"})
        for i, word in enumerate(diki.other_words)
    ]

    return diki.data.to_dict("records"), options, [], diki.popularity, badges


# 2️⃣ podgląd zaznaczonych fiszek ----------------------------------------------
@app.callback(
    Output("output-1-div", "children"),
    Input("checklist-polish-words", "value"),
    State("translation", "data"),
    prevent_initial_call=True,
)
def preview(selected, translation):
    if not selected or not translation:
        return None
    df = pd.DataFrame(translation)
    try:
        chosen = df.iloc[selected]
    except IndexError:
        return "Błąd indeksu."

    rows = []
    for _, r in chosen.iterrows():
        front = [r.polish_word]
        if r.pol_example:
            front += [html.Br(), html.Br(), r.pol_example]
        back = [r.english_word, html.Br(), r.pronunciation]
        if r.eng_example:
            back += [html.Br(), html.Br(), r.eng_example]

        rows.append(
            dbc.Row(
                [
                    dbc.Col(dbc.Card(dbc.CardBody(html.P(front, className="card-text text-center")), color="warning", outline=True), width=6),
                    dbc.Col(dbc.Card(dbc.CardBody(html.P(back, className="card-text text-center")), color="warning", outline=True), width=6),
                ],
                className="g-3 mb-3",
            )
        )
    return rows


# 3️⃣ zaznacz / odznacz wszystko ------------------------------------------------
@app.callback(
    Output("checklist-polish-words", "value", allow_duplicate=True),
    Input("select-all-button", "n_clicks"),
    State("checklist-polish-words", "options"),
    prevent_initial_call=True,
)
def select_all(n, options):
    if not n:
        raise dash.exceptions.PreventUpdate
    return [o["value"] for o in options]


@app.callback(
    Output("checklist-polish-words", "value", allow_duplicate=True),
    Input("deselect-all-button", "n_clicks"),
    prevent_initial_call=True,
)
def deselect_all(n):
    if not n:
        raise dash.exceptions.PreventUpdate
    return []


# 4️⃣ włączanie „Dodaj fiszki” ----------------------------------------------------
@app.callback(
    Output("send-button", "disabled"),
    Input("checklist-polish-words", "value"),
)
def toggle_send(v):
    return not bool(v)


# 5️⃣ dodawanie fiszek do pamięci -------------------------------------------------
@app.callback(
    [Output("input-word", "value"), Output("saved-flashcards", "data", allow_duplicate=True), Output("n-rows", "children", allow_duplicate=True)],
    Input("send-button", "n_clicks"),
    [State("translation", "data"), State("checklist-polish-words", "value"), State("saved-flashcards", "data")],
    prevent_initial_call=True,
)
def add(n, translation, ids, store):
    if not n or not ids or not translation:
        raise dash.exceptions.PreventUpdate
    df = pd.DataFrame(translation)
    try:
        chos = df.iloc[ids]
    except IndexError:
        raise dash.exceptions.PreventUpdate

    chos = chos.assign(
        front=lambda d: d.polish_word + d.pol_example.fillna("").apply(lambda x: f"<br><br><small>{x}</small>" if x else ""),
        back=lambda d: d.english_word + "<br>" + d.pronunciation + d.eng_example.fillna("").apply(lambda x: f"<br><br><small>{x}</small>" if x else ""),
    )
    new = chos[["front", "back"]].to_dict("records")
    store = store + new
    return "", store, len(store)


# 6️⃣ aktywacja przycisku pobierania ---------------------------------------------
@app.callback(
    Output("download", "disabled"),
    Input("n-rows", "children"),
)
def toggle_download(n):
    try:
        return int(n) <= 0
    except (TypeError, ValueError):
        return True


# 7️⃣ pobieranie i czyszczenie ----------------------------------------------------
@app.callback(
    [Output("download-file", "data"), Output("saved-flashcards", "data", allow_duplicate=True), Output("n-rows", "children", allow_duplicate=True)],
    Input("download", "n_clicks"),
    State("saved-flashcards", "data"),
    prevent_initial_call=True,
)
def download(n, data):
    if not n or not data:
        raise dash.exceptions.PreventUpdate
    df = pd.DataFrame(data)
    payload = dcc.send_data_frame(df.to_csv, "flashcards.txt", index=False, header=False, sep=";")
    return payload, [], 0


# 8️⃣ klik w badge alternative word ---------------------------------------------
@app.callback(
    Output("input-word", "value", allow_duplicate=True),
    Input({"type": "otherword-badge", "index": ALL}, "n_clicks"),
    State({"type": "otherword-badge", "index": ALL}, "children"),
    prevent_initial_call=True,
)
def badge_fill(clicks, labels):
    if not clicks or not any(clicks):
        raise dash.exceptions.PreventUpdate
    triggered = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    idx = json.loads(triggered)["index"]
    return labels[idx]


if __name__ == "__main__":
    app.run_server(debug=True)
