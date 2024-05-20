
from data.fill_schedules import fill_schedules, generate_schedules
from data.np_data_fetch import parse_nord_pool_data
from data.refresh_outdated_schedules import refresh_outdated_schedules
from data.search_for_available_schedules import search_for_available_schedules

print("Starting heroku scheduler")
parse_nord_pool_data("LV")
refresh_outdated_schedules()
search_for_available_schedules()
generate_schedules()
fill_schedules()
print("Cron job finished")