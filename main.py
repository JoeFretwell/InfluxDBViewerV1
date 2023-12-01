from tkinter import *
from tkinter import messagebox, ttk

import pandas
import pandastable
from pandastable import Table, TableModel
from influxdb_client import InfluxDBClient
from influxdb_client.rest import ApiException
import pandas as pd
import warnings
from influxdb_client.client.warnings import MissingPivotFunction
warnings.simplefilter("ignore", MissingPivotFunction)
import tkinter
from tkinter.filedialog import asksaveasfilename


def logincheck():
    with InfluxDBClient(url=URLEntry.get(), token=authTokenEntry.get(), org=orgEntry.get()) as client:
        global org
        org = orgEntry.get()

        #check connection
        print("> Checking connection ...", end=" ")
        try:
            client.api_client.call_api('/ping', 'GET')
        except:
            tkinter.messagebox.showerror(title= 'Error', message =
            'Cannot connect to server. is your URL correct? e.g http://localhost:8086 ')
            raise Exception("cannot connect. Are you sure your URL is correct?")
        print("ok")

        #check query
        print("> Checking credentials for query ...", end=" ")
        try:
            client.query_api().query(f"from(bucket:\"{bucketEntry.get()}\") |> range(start: -1m) |> limit(n:1)", org)
        except ApiException as e:
            # missing credentials
            if e.status == 404:
                tkinter.messagebox.showerror(title='Error', message=
                'Cannot Find specified bucket.')
                raise Exception(
                    f" '{bucketEntry.get()}' doesn't exist.") from e
            if e.status == 401:
                tkinter.messagebox.showerror(title='Error', message=
                "the token does not have sufficient credentials to read from the specified bucket.")
                raise Exception(f"The specified token doesn't have sufficient credentials to read from '{bucketEntry.get()}'") from e

            if e.status == 400:
                tkinter.messagebox.showerror(title='Error', message=
                'Cannot Find specified organisation')
                raise Exception(f"Cannot find the organisation '{orgEntry.get()}'") from e
            raise

        print("Connection and Token OK!")
        successLabel = tkinter.Label(frame1, text='Login successful', bg='#333333', fg='#259b28', font=("Arial", 15))
        successLabel.grid(row = 5, column = 0)
        global bucket
        bucket = bucketEntry.get()

        query = f"""
        import \"influxdata/influxdb/schema\"

        schema.measurements(bucket: \"{bucket}\")
        """

        print(f'Query: \n {query}')

        query_api = client.query_api()
        tables = query_api.query(query=query, org=org)

        measurements = [row.values["_value"] for table in tables for row in table]
        measurementLabel = tkinter.Label(frame2, text="Which Measurement", bg='#333333', fg='#FFFFFF', font=("Arial", 16))
        global measurementEntry
        measurementEntry = ttk.Combobox(frame2, values=measurements, font=("Arial", 16))
        measurementEntry.set(measurements[0])

        measurementLabel.grid(row=2, column=0)
        measurementEntry.grid(row=2, column=1, pady=10)
        #frame2.grid(row=1, column=0, sticky='news')
        frame1.pack_forget()
        frame2.pack(side = TOP)
        tkinter.messagebox.showinfo(title='Successfully logged in.', message=
                'Successfully logged into the InfluxDB server. Now select your desired time range and measurement from your bucket to view.')



    pass

def showtable():
    client = InfluxDBClient(url=URLEntry.get(), token=authTokenEntry.get(), org=orgEntry.get())
    timeEntryget = timeEntry.get()
    query_api = client.query_api()

    query = """ from(bucket:"{bucket}")\
    |> range(start: -{timeEntry}h)\
    |> filter(fn:(r) => r._measurement == "{measurementEntry}")""".format(bucket = bucket, timeEntry = timeEntryget, measurementEntry = measurementEntry.get())
    global result
    result = client.query_api().query_data_frame(org=org, query=query)


    #make table

    if type(result) == list:
        result = pandas.concat(result)
    cols = list(result.columns)

    tree = ttk.Treeview(frame3, selectmode='extended')
    tree.place(relx = 0.01, rely = 0.128, width = 646, height = 410)
    tree["columns"] = cols
    print(cols)
    for i in cols:
        tree.column(i, anchor="w")
        tree.heading(i, text=i, anchor='w')

    for index, row in result.iterrows():
        tree.insert("", 0, text=index, values=list(row))

    #make scrollbars
    vsb = ttk.Scrollbar(frame3, orient="vertical", command=tree.yview)
    vsb.place(relx = 0.934, rely = 0.128, width = 22, height = 432)

    hsb = ttk.Scrollbar(frame3, orient="horizontal", command=tree.xview)
    hsb.place(relx = 0.002, rely = 0.922, width = 651, height = 22)

    frame2.pack_forget()
    frame3.pack(side = TOP)
    pass



window = tkinter.Tk()
window.title("InfluxDB Table Viewer")
window.configure(bg = '#333333')
window.resizable(False,False)

frame1 = tkinter.Frame(window, bg = '#333333')

frame2 = tkinter.Frame(window, bg = '#333333')

frame3 = tkinter.Frame(window, height=520, width=700 )

#Login Widgets
loginLabel = tkinter.Label(frame1, text = 'Login', bg = '#333333', fg='#FFFFFF', font=("Arial",30))

URLLabel = tkinter.Label(frame1, text = "InfluxDB URL:", bg = '#333333', fg='#FFFFFF', font=("Arial",16))
URLEntry = tkinter.Entry(frame1, font=("Arial",16))

authTokenLabel = tkinter.Label(frame1, text = "Token:", bg = '#333333', fg='#FFFFFF', font=("Arial",16))
authTokenEntry = tkinter.Entry(frame1, font=("Arial",16))

orgLabel = tkinter.Label(frame1, text = "Organisation:", bg = '#333333', fg='#FFFFFF', font=("Arial",16))
orgEntry = tkinter.Entry(frame1, font=("Arial",16))

bucketLabel= tkinter.Label(frame1, text = "Bucket:", bg = '#333333', fg='#FFFFFF', font=("Arial",16))
bucketEntry = tkinter.Entry(frame1, font=("Arial",16))

loginButton = tkinter.Button(frame1, text = "Login", font=("Arial",16), command = logincheck)



#place login widgets
loginLabel.grid(row =0, column =0, columnspan =2, sticky='news', pady=30,padx = 40)

URLLabel.grid(row =1, column =0,padx = 40)
URLEntry.grid(row =1, column =1, pady =10,padx = 40)

authTokenLabel.grid(row =2, column =0,padx = 40)
authTokenEntry.grid(row =2, column =1, pady =10,padx = 40)

orgLabel.grid(row =3, column =0,padx = 40)
orgEntry.grid(row =3, column =1, pady =10,padx = 40)

bucketLabel.grid(row =4, column =0,padx = 40)
bucketEntry.grid(row =4, column =1, pady =10,padx = 40)

loginButton.grid(row =5, column =1, columnspan=2, pady =30)

frame1.pack(side = TOP)
#frame 2 contents


chooseParamsLabel = tkinter.Label(frame2, text = 'Filter your results', bg = '#333333', fg='#FFFFFF', font=("Arial",30))

timeLabel = tkinter.Label(frame2, text = "How many hours of data from the present?", bg = '#333333', fg='#FFFFFF', font=("Arial",16))
timeEntry = tkinter.Entry(frame2, font=("Arial",16))



timeLabel.grid(row =1, column =0,)
timeEntry.grid(row =1, column =1,pady = 10,padx = 5)

submitButton = tkinter.Button(frame2, text = "Submit", font=("Arial",16), command = showtable)
submitButton.grid(row =3, column =1,padx = 40)


#Frame 3 buttons

def goBack():
    frame3.pack_forget()
    frame2.pack()
    pass

def exportTable():
    filename = asksaveasfilename(filetype=[('CSV files', '*.csv')])

    filenameFinal=filename + '.csv'
    result.to_csv(filenameFinal, index = False)

goBackButton = tkinter.Button(frame3, text = 'back', command = goBack)
exportButton = tkinter.Button(frame3, text = 'Export as CSV', command = exportTable)

goBackButton.place(relx = 0.05, rely = 0.05)
exportButton.place(relx = 0.4, rely = 0.05)

window.mainloop()