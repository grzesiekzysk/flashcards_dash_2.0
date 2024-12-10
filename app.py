import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, html

app = dash.Dash(
    external_stylesheets=[dbc.themes.DARKLY]
)

app.layout = dbc.Container(
    [

        dbc.Label("Toggle a bunch", className="text-light"),
        dbc.InputGroup(
            [
                dbc.InputGroupText(
                    "🇬🇧", 
                    className="text-light bg-dark"
                ), 
                dbc.Input(
                    placeholder="Username", 
                    className="bg-dark text-light"
                )
            ],
            className="mb-3",
        ),
        dbc.Checklist(
            options=[
                {"label": "Option 1", "value": 1},
                {"label": "Option 2", "value": 2},
            ],
            value=[1],
            id="switches-input",
            switch=True,
            inputClassName="bg-dark",
            labelClassName="text-light"  # aby tekst przy etykietach był jasny

        )
    ],
    className="p-5",
)

if __name__ == "__main__":
    app.run_server(debug=True)
