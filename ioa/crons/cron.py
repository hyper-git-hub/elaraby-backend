from ioa.crons.scheduler import *
from datetime import timedelta
# Data from ActivityList to aggregation
def aggregetion_data(self):
    time_range = datetime.date.today() - timedelta(days=1)
    return testing(date_range=time_range)
