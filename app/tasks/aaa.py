
from settings import SHEET_ID_INSTAGRAM

from app.server.helpers import gspread


if __name__ == '__main__':
    response = gspread.get_sheet_values(SHEET_ID_INSTAGRAM, "hashtag", "FORMULA")
    label_list, hashtag_list = gspread.convert_to_dict_data(response)
    body = {'values': gspread.convert_to_sheet_values(label_list, hashtag_list)}
    gspread.update_sheet_values(SHEET_ID_INSTAGRAM, 'hashtag', body)
    print("SUCCESS!! update_hashtag")
