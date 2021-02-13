import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from roboclimate.weather_spider import collect_current_weather_data, collect_five_day_weather_forecast_data, init
import roboclimate.config as config
import roboclimate.util as util
from roboclimate.data_analysis import analyse_data
from roboclimate.notebook_publisher import publish_notebook

logging.basicConfig(filename='roboclimate.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level='INFO')

init(config.csv_folder, config.csv_header, config.cities.keys())

scheduler = BlockingScheduler()
scheduler.add_job(collect_current_weather_data, 'cron', [util.current_utc_date_generator, config.cities, config.csv_folder, config.tolerance], hour='*/3')
scheduler.add_job(collect_five_day_weather_forecast_data, 'cron', [
                  util.current_utc_date_generator, config.cities, config.csv_folder, config.tolerance], hour=22)
scheduler.add_job(analyse_data, 'cron', [], hour=22, minute=30)
scheduler.add_job(publish_notebook, 'cron', [], hour=23)
scheduler.start()
