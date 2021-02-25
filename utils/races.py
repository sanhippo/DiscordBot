import gspread

gc = gspread.service_account()

workbook = gc.open("Desolation Player Management")
sheet_races = workbook.worksheet("Races")

batch_races_data = None
uniquelist = None


def getallraces():
	global batch_races_data
	if batch_races_data is None:
		batch_races_data = sheet_races.get_all_records()
	return batch_races_data


def getuniqueraces(racelist):
	global uniqueraces
	if uniqueraces is None:
		uniqueraces = set(val for dic in racelist for val in dic.values())
	return uniqueraces
