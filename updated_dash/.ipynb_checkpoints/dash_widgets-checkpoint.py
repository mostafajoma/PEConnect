import ipywidgets as widgets
from IPython.display import display

# To select portfolio plots/info
risk_selector = widgets.Dropdown(
    options = ['Conservative', 'Moderate', 'Aggressive'],
    value = 'Conservative',
    description = 'Risk Tolerance',
    style = {'description_width': 'initial'},
    disabled = False
)

time = widgets.IntText(
    value = 1,
    description = 'Time Frame'
)

time_selector = widgets.Dropdown(
    options = ['year(s)', 'month(s)', 'day(s)'],
    value = 'year(s)'
)

button = widgets.Button(
    description = 'Update',
    layout = {'border': '1px solid black'}
)