import xlwings as xw
import pickle


def read_data_from_excel(file_path, sheet_name):
    # Open the Excel file
    app = xw.App(visible=False)  # Open Excel in the background without displaying it
    workbook = app.books.open(file_path)
    sheet = workbook.sheets[sheet_name]

    # Read the data from the Excel sheet
    data = sheet.range("A1").expand("table").value

    # Close the workbook and the Excel application
    workbook.close()
    app.quit()

    return data


def update_pickle_from_excel(pickle_file, excel_file, sheet_name):
    # Load the pickle object
    with open(pickle_file, 'rb') as f:
        pickle_object = pickle.load(f)

    # Read data from Excel
    excel_data = read_data_from_excel(excel_file, sheet_name)

    # Update the pickle object with the data from Excel
    # (Assuming that the pickle object is a dictionary and we want to update its keys and values)
    for key, value in excel_data.items():
        pickle_object[key] = value

    # Save the updated pickle object back to the file
    with open(pickle_file, 'wb') as f:
        pickle.dump(pickle_object, f)


if __name__ == "__main__":
    pickle_file_path = 'path/to/your/pickle_file.pickle'
    excel_file_path = 'path/to/your/excel_file.xlsx'
    sheet_name = 'Sheet1'

    update_pickle_from_excel(pickle_file_path, excel_file_path, sheet_name)
