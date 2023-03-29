import numpy as np
import streamlit as st
import roboclimate.data_explorer as rdq
import roboclimate.config as rconf
import matplotlib.pyplot as plt

padding = 0
st.set_page_config(page_title="Roboclimate", layout="wide")


def plot_actual_vs_forecast(days):
    fig, ax = plt.subplots()
    plt.grid(True)
    city = rconf.cities[city_name_option]
    join_data_df = rdq.load_csv_files(city, weather_var_option)["join_data_df"]
    N = join_data_df.shape[0]
    max_x = N
    min_x = max_x - (rconf.day_factor * days)
    print(f"min_x={min_x}")
    print(f"max_x={max_x}")
    max_y = max(max(join_data_df[weather_var_option][min_x:max_x]), max(join_data_df[tn][min_x:max_x]))
    min_y = min(min(join_data_df[weather_var_option][min_x:max_x]), min(join_data_df[tn][min_x:max_x]))
    print(f"min_y={min_y}")
    print(f"max_y={max_y}")
    x = np.linspace(0, max_x - min_x, max_x - min_x)
    plt.xlim(0, max_x - min_x)
    plt.ylim(min_y, max_y)
    # [l.remove() for l in ax.lines]
    # [l.remove() for l in ax.lines]
    plt.plot(x, join_data_df[weather_var_option][min_x:max_x], label=f'actual {weather_var_option}', color='green', marker="o")
    plt.plot(x, join_data_df[tn][min_x:max_x], label=tn, color='red', marker='*')
    plt.title(f"{city_name_option}: t vs {tn} (last {days} days)")
    plt.legend()
    st.pyplot(fig)


def plot_metrics():
    fig, ax = plt.subplots()
    plt.grid(True)
    city = rconf.cities[city_name_option]
    metrics_df = rdq.load_csv_files(city, weather_var_option)["metrics_df"]
    # plt.rcParams['figure.figsize'] = (7,3)
    x = np.linspace(0, 1, 5)
    ax.set_xticks(x)
    ax.set_xticklabels(['t5', 't4', 't3', 't2', 't1'])
    max_y = max(max(metrics_df['mae']), max(metrics_df['rmse']), max(metrics_df['medae']))
    min_y = min(min(metrics_df['mae']), min(metrics_df['rmse']), min(metrics_df['medae']))
    # print(f"min_y={min_y}")
    # print(f"max_y={max_y}")
    plt.ylim(min_y - .5, max_y + .5)
    # [l.remove() for l in ax.lines]
    # [l.remove() for l in ax.lines]
    # [l.remove() for l in ax.lines]
    plt.plot(x, metrics_df['mae'], label='mae', color='blue', marker='o')
    plt.plot(x, metrics_df['rmse'], label='rmse', color='grey', marker='^')
    plt.plot(x, metrics_df['medae'], label='medae', color='red', marker='*')
    plt.title(f"metrics - {city_name_option}")
    plt.legend()
    st.pyplot(fig)


def plot_scaled_error():
    fig, ax = plt.subplots()
    plt.grid(True)
    city = rconf.cities[city_name_option]
    metrics_df = rdq.load_csv_files(city, weather_var_option)["metrics_df"]
    x = np.linspace(0, 1, 5)
    ax.set_xticks(x)
    ax.set_xticklabels(['t5', 't4', 't3', 't2', 't1'])
    # [l.remove() for l in ax.lines]
    # [l.remove() for l in ax.lines]
    plt.plot(x, metrics_df['mase'], label='mase', color='blue', marker='o')
    # plt.plot(x, metrics_df['mase1y'], label='mase1y', color='black', marker='*')
#     plt.plot(x, df["metrics_df"]['mase1y_avg'], label='mase1y_avg', color='black', marker='o')
    plt.plot(x, np.ones(5), label='1', color='red')
    plt.title(f"Mean Absolute Scaled Error - {city_name_option}")
    plt.legend()
    st.pyplot(fig)


def plot_cities():
    fig, ax = plt.subplots()
    plt.grid(True)
    # plt.rcParams['figure.figsize'] = (7,3)
    colors = ['blue', 'red', 'green', 'black', 'purple']
    x = np.linspace(0, 1, 5)
    ax.set_xticks(x)
    ax.set_xticklabels(['t5', 't4', 't3', 't2', 't1'])
    idx = 0
#     plt.plot(x, np.ones(5), label='1', color='red')
    # for city in rconf.cities.values():
        # [l.remove() for l in ax.lines]
    for city in rconf.cities.values():
        files = rdq.load_csv_files(city, weather_var_option)
        plt.plot(x, files["metrics_df"][metric_option], label=city.name, marker='o')
        idx += 1
    plt.title(metric_option)
    plt.legend()
    st.pyplot(fig)


with st.sidebar:
    tn = st.selectbox(
        'select tx forecast',
        ['t1', 't2', 't3', 't4', 't5'])

    weather_var_option = st.selectbox(
        'choose a weather variable',
        [wvar for wvar in rconf.weather_variables.values()])

    city_name_option = st.sidebar.selectbox(
        'select a city',
        [city.name for city in rconf.cities.values()])


metric_option = st.sidebar.selectbox(
    'select metric to compare among all cities',
    ['mae','rmse','medae','mase'])


st.title('Roboclimate')
st.header('Forecast analysis by city')


col1, col2 = st.columns([1,1.2])
with col1:
    plot_actual_vs_forecast(20)


col1, col2, col3 = st.columns(3)
with col1:
    plot_metrics()

with col2:
    plot_scaled_error()



st.header('Forecast comparison among cities')
col1, col2 = st.columns(2)
with col1:
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

st.write("This is outside the container")

# with st.empty():
#     for seconds in range(3):
#         st.write(f"⏳ {seconds} seconds have passed")
#         time.sleep(1)
#     st.write("✔️ 1 minute over!")
