"""Streamlit dashboard
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from streamlit_option_menu import option_menu
import roboclimate.data_explorer as rde
import roboclimate.config as rconf

PADDING = 0
st.set_page_config(page_title="Roboclimate", layout="wide")


@st.cache_data
def fetch_actual_vs_forecast_data(city_name, weather_variable, tn, last_n_days: int):
    city: rconf.City = rconf.cities[city_name]
    join_data_df: pd.DataFrame = rde.load_csv_files(city, weather_variable)["join_data_df"]
    N = join_data_df.shape[0]
    max_x = N
    min_x = max_x - (rconf.day_factor * last_n_days)
    print(f"min_x={min_x}")
    print(f"max_x={max_x}")
    if tn != 'None':
        max_y = max(pd.concat([join_data_df[weather_var_option1][min_x:max_x], join_data_df[tn][min_x:max_x]]))
        min_y = min(pd.concat([join_data_df[weather_var_option1][min_x:max_x], join_data_df[tn][min_x:max_x]]))
    else:
        max_y = max(join_data_df[weather_var_option1][min_x:max_x])
        min_y = min(join_data_df[weather_var_option1][min_x:max_x])
    print(f"min_y={min_y}")
    print(f"max_y={max_y}")
    x = np.linspace(0, max_x - min_x, max_x - min_x)
    y1 = join_data_df[weather_var_option1][min_x:max_x]
    y2 = None
    if tn != 'None':
        y2 = join_data_df[tn][min_x:max_x]
    return (x, y1, y2, (min_x, max_x), (min_y, max_y))


def plot_actual_vs_forecast(city_name_option1, weather_var_option1, tn, last_n_days):
    x, y1, y2, (min_x, max_x), (min_y, max_y) = \
        fetch_actual_vs_forecast_data(city_name_option1, weather_var_option1, tn, last_n_days)

    fig, ax = plt.subplots()
    plt.grid(True)
    plt.xlim(0, max_x - min_x)
    plt.ylim(min_y, max_y)
    plt.xlabel('# points')
    plt.ylabel(weather_var_option1)
    plt.plot(x, y1.to_numpy(), label=f'actual {weather_var_option1}', color='green', marker="o", markersize=3)
    if tn != 'None':
        plt.plot(x, y2.to_numpy(), label=tn, color='red', marker='*', markersize=3)
    plt.title(f"{city_name_option1}: t vs {tn} (last {last_n_days} days)")
    plt.legend()
    st.pyplot(fig)


@st.cache_data
def fetch_metrics_data(city_name, weather_variable):
    city = rconf.cities[city_name]
    metrics_df = load_metrics_file(city, weather_variable)
    x = np.linspace(0, 1, 5)
    max_y = max(pd.concat([metrics_df['mae'], metrics_df['rmse'], metrics_df['medae']]))
    min_y = min(pd.concat([metrics_df['mae'], metrics_df['rmse'], metrics_df['medae']]))
    return (x, metrics_df['mae'], metrics_df['rmse'], metrics_df['medae'], metrics_df['mase'], (min_y, max_y))


def plot_metrics(city_name, weather_variable):
    x, y_mae, y_rmse, y_medae, y_mase, (min_y, max_y) = fetch_metrics_data(city_name, weather_variable)

    fig, ax = plt.subplots()
    plt.grid(True)
    ax.set_xticks(x)
    ax.set_xticklabels(['t5', 't4', 't3', 't2', 't1'])
    plt.ylim(min_y - .5, max_y + .5)
    plt.plot(x, y_mae.to_numpy(), label='mae', color='blue', marker='o')
    plt.plot(x, y_rmse.to_numpy(), label='rmse', color='grey', marker='^')
    plt.plot(x, y_medae.to_numpy(), label='medae', color='red', marker='*')
    plt.title(f"forecast errors - {city_name}")
    plt.legend()
    st.pyplot(fig)


def plot_scaled_error():
    fig, ax = plt.subplots()
    plt.grid(True)
    city: rconf.City = rconf.cities[city_name_option2]
    metrics_df: pd.DataFrame = load_metrics_file(city, weather_var_option2)
    x = np.linspace(0, 1, 5)
    ax.set_xticks(x)
    ax.set_xticklabels(['t5', 't4', 't3', 't2', 't1'])
    plt.plot(x, metrics_df['mase'].to_numpy(), label='mase', color='blue', marker='o')
    plt.plot(x, np.ones(5), label='1', color='red')
    plt.title(f"Mean Absolute Scaled Error - {city_name_option2}")
    plt.legend()
    st.pyplot(fig)


@st.cache_data
def load_metrics_file(city, weather_var):
    return rde.load_metrics_file(city, weather_var)


def plot_cities():
    fig, ax = plt.subplots()
    plt.grid(True)
    # plt.rcParams['figure.figsize'] = (7,3)
    x = np.linspace(0, 1, 5)
    ax.set_xticks(x)
    ax.set_xticklabels(['t5', 't4', 't3', 't2', 't1'])
    idx = 0
    for city in cities_option:
        metrics_df = load_metrics_file(rconf.cities[city], weather_var_option3)
        plt.plot(x, metrics_df[metric_option].to_numpy(), label=city, marker='o')
        idx += 1
    plt.title(metric_option)
    plt.legend()
    st.pyplot(fig)


#################################################
################## LAYOUT #######################
#################################################

with st.sidebar:
    selected = option_menu('Roboclimate', ["Intro", 'Forecast vs Actual', 'Forecast Metrics', 'City Comparison'],
                           icons=['play-btn', 'cloud-rain', 'thermometer-sun', 'building'], menu_icon='tropical-storm', default_index=0)

    if selected == 'Forecast vs Actual':
        st.markdown('---')  # Horizontal line for visual separation
        tn = st.selectbox(
            'select $t_j$ forecast',
            ['t1', 't2', 't3', 't4', 't5', 'None'])

        weather_var_option1 = st.selectbox(
            'choose a weather variable',
            list(rconf.weather_variables.values()),
            key='weather_var_option1')

        city_name_option1 = st.sidebar.selectbox(
            'select a city',
            [city.name for city in rconf.cities.values()],
            key='city_name_option1')

    if selected == 'Forecast Metrics':
        st.markdown('---')  # Horizontal line for visual separation

        weather_var_option2 = st.selectbox(
            'choose a weather variable',
            list(rconf.weather_variables.values()),
            key='weather_var_option2')

        city_name_option2 = st.sidebar.selectbox(
            'select a city',
            [city.name for city in rconf.cities.values()],
            key='city_name_option2')

    if selected == 'City Comparison':
        st.markdown('---')  # Horizontal line for visual separation

        weather_var_option3 = st.selectbox(
            'choose a weather variable',
            list(rconf.weather_variables.values()),
            key='weather_var_option3')

        metric_option = st.sidebar.selectbox(
            'select metric to compare among all cities',
            ['mae', 'rmse', 'medae', 'mase'])

        cities_option = st.multiselect(
            'select cities to compare',
            [city.name for city in rconf.cities.values()],
            ['london'])


if selected == 'Intro':
    st.title('Welcome to Roboclimate')
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            """
            Roboclimate is a website to evaluate the accuracy of weather models according to the values forecast for multiple variables (temperataure, pressure, etc.) measured in different cities across the world (i.e. London, Madrid, Sydney...)  

            The forecast model under consideration is [OpenWeather's](https://openweathermap.org).     
            """
        )

        st.header('Methodology')
        st.markdown(
            """
            Weather measurements are taken at 3-hour intervals from midnight until 9pm every day, totalling 8 datapoints per day.
            Also every day, we obtain the forecast for the next 5 days (resulting in new 5*8 datapoints per day)

            This way each measurement can be compared to the values forecast during the previous 5 days. 
            Those values will be denoted as $t_1$ (forecast made 1 day ago), $t_2$ (forecast made 2 days ago) and so on up to $t_5$.            
            For simplicity, we will refer to them as $t_j$ where $j = 1, 2, ..., 5$, whereas $t$ will be the real value.
            """
        )
        st.subheader('Metrics')
        st.markdown(
            """
            In order to evaluate the accuracy of each forecast $t_j$, the following metrics are computed:

            ##### Mean Absolute Error (MAE)
            Average of the absolute value of the errors (_errors_ are the difference between real and forecast values)                                                
            """
        )
        st.latex(r"{mae}_j = \frac{1}{n} \sum_{i=1}^{n} |t_i - t_{ji}|")

        st.markdown(
            """
            ##### Root Mean Squared Error (RMSE)
            Square root of the average of the square of the errors. It weighs outliers more heavily than MAE as a result of the squaring of each term.
            """
        )
        st.latex(r"{rmse}_j = \sqrt{\frac{1}{n} \sum_{i=1}^{n} (t_i - t_{ji})^2}")

        st.markdown(
            """
            ##### Median absolute error (MEDAE)
            Median of the absolute value of the errors.

            It is robust to outliers
            """
        )
        st.latex(r"{mdae}_j = \text{median} \left( |t_i - t_{ji}| \right)_{i=1}^{n}")

        st.markdown(
            """
            ##### Mean Absolute Scaled Error (MASE)
            [MASE](https://en.wikipedia.org/wiki/Mean_absolute_scaled_error) is a measure of the precision of a model compared to the naive forecast.
            It is calculated as the MAE of the forecast divided by the MAE of the naive forecast.            

            Therefore, $mase_j > 1$ indicates that the naive forecast performs better than the model. 

            Naive forecasting models are based exclusively on historical observation, e.g. the forecast for tomorrow is today's value.

            In our case, the naive forecast corresponding to the forecast $t_j$ is the value actually measured $j$ days before.
            """
        )
        st.latex(r"{mase}_j = \frac{\frac{1}{n} \sum_{i=1}^{n} |t_i - t_{ji}|}{\frac{1}{n-8j} \sum_{i=8j+1}^{n} |t_i - t_{i-8j}|}")
        st.markdown("""where 8 is the number of measurements per day""")

if selected == 'Forecast vs Actual':
    last_n_days = 20
    col1, col2 = st.columns([0.7, 0.3])
    with col1:
        plot_actual_vs_forecast(city_name_option1, weather_var_option1, tn, last_n_days)
    with col2:
        with st.expander("Show data"):
            x, y1, y2, (min_x, max_x), (min_y, max_y) = \
                fetch_actual_vs_forecast_data(city_name_option1, weather_var_option1, tn, last_n_days)

            st.dataframe(pd.concat([y1, y2], axis=1))

if selected == 'Forecast Metrics':
    x, y_mae, y_rmse, y_medae, y_mase, (min_y, max_y) = fetch_metrics_data(city_name_option2, weather_var_option2)
    col1, col2 = st.columns(2)
    with col1:
        plot_metrics(city_name_option2, weather_var_option2)
        with st.expander("Show data"):
            st.dataframe(pd.concat([y_mae, y_rmse, y_medae], axis=1))

    with col2:
        plot_scaled_error()
        with st.expander("Show data"):
            st.dataframe(y_mase)

    # plot_metrics()
    # plot_scaled_error()

if selected == 'City Comparison':
    # col1, col2 = st.columns(2)
    # with col1:
    plot_cities()

# with st.sidebar:
#     with st.echo():
#         st.write("This code will be printed to the sidebar.")

#     with st.spinner("Loading..."):
#         time.sleep(5)
#     st.success("Done!")

# with st.container():
#    plot_metrics()
#    plot_scaled_error()
#    plot_actual_vs_forecast(20)

# st.write("This is outside the container")

# with st.empty():
#     for seconds in range(3):
#         st.write(f"⏳ {seconds} seconds have passed")
#         time.sleep(1)
#     st.write("✔️ 1 minute over!")
