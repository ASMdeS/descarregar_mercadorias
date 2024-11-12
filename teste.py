import datetime
import os
import pandas as pd
import streamlit as st
import mysql.connector
from mysql.connector import Error
from datetime import time


def get_finishing_time(start_date, start_time, type):
    # Define offloading durations for each type
    offloading_duration = {
        "Pallet Monoproduto": datetime.timedelta(minutes=30),
        "Pallet Misto": datetime.timedelta(minutes=60),
        "Estivado": datetime.timedelta(minutes=120)
    }

    # Combine start_date and start_time into a single datetime object
    start_datetime = datetime.datetime.combine(start_date, start_time)

    # Retrieve the offloading time for the specified type
    # Default to zero timedelta if the type is not found
    duration = offloading_duration.get(type, datetime.timedelta())

    # Calculate end_time by adding the offloading duration to start_datetime
    end_time = start_datetime + duration

    # Return only the time component
    return end_time.time()




# Fetch MySQL connection details from secrets
db_config = {
    "host": st.secrets["mysql"]["host"],
    "user": st.secrets["mysql"]["username"],
    "password": st.secrets["mysql"]["password"],
    "database": st.secrets["mysql"]["database"],
    "port": st.secrets["mysql"]["port"],
}

# Function to establish a connection
def create_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as e:
        st.error(f"Error connecting to MySQL: {e}")
        return None

# Function to insert a new schedule into MySQL
def insert_schedule(schedule_data):
    conn = create_connection()
    if conn is not None:
        cursor = conn.cursor()
        insert_query = """
            INSERT INTO Schedules 
            (ID, Supplier_Name, Invoice_Number, Dropoff_Date, Dropoff_Time, Status, Distribution_Center, Load_Type, 
            Pallet_Number, Total_Weight, SKU_Count, Created_At) 
            VALUES (%(ID)s, %(Supplier_Name)s, %(Invoice_Number)s, %(Dropoff_Date)s, %(Dropoff_Time)s, %(Status)s, 
                    %(Distribution_Center)s, %(Load_Type)s, %(Pallet_Number)s, %(Total_Weight)s, %(SKU_Count)s, %(Created_At)s);
        """
        try:
            cursor.execute(insert_query, schedule_data)
            conn.commit()
            st.success("Agendamento enviado! Aqui estão os detalhes:")
            st.dataframe(pd.DataFrame([schedule_data]), use_container_width=True, hide_index=True)
        except Error as e:
            st.error(f"Erro ao inserir o agendamento: {e}")
        finally:
            cursor.close()
            conn.close()
    else:
        st.error("Could not establish a database connection.")


# Set the page configuration
st.set_page_config(page_title="Agendamento de Entrega", page_icon="📅")
st.title("📅 Agendamento de Entrega")
st.divider()
st.subheader("Regras gerais para entrega")
st.write(
    """
•	Não acataremos divergências de preços e/ou quantidades (nestes casos emitiremos a NF devolução parcial), ou de prazo e/ou produtos sem cadastro (neste caso realizaremos a recusa total da NF). \n
•	No ato do recebimento das mercadorias, se caso houver avarias, faltas ou inversão de produtos, emitiremos de imediato a nota fiscal de devolução, sem a necessidade de contatar a indústria e entregaremos ao motorista responsável pela entrega. \n
•	O shelf-life para o recebimento de mercadorias é de no mínimo 70% em diante da data de fabricação. Abaixo deste percentual efetuaremos a nota fiscal de devolução destes itens.\n
•	Será cobrado um valor por palete/por tonelada descarregada, de acordo com a tabela:
    """
)


dicionario_precos = {
    "Tipo da carga": ["Pallet monoproduto", "Pallet misto", "Estivado (por tonelada)"],
    "Valor unitário": ["R$ 35,00", "R$ 45,00", "R$ 62,00"]
}

# Creating the DataFrame
dataframe_precos = pd.DataFrame(dicionario_precos)
st.table(dataframe_precos)

# Define the path for the CSV file
csv_file_path = "schedules.csv"

# Load existing schedules from CSV or create a new dataframe
if os.path.exists(csv_file_path):
    df = pd.read_csv(csv_file_path)
else:
    # Create an empty dataframe with the necessary columns
    df = pd.DataFrame(
        columns=["ID", "Indústria", "Número da NF", "Drop-off Date", "Drop-off Time", "Finishing Time", "Status",
                 "Centro de Distribuição", "Tipo de Carga",
                 "Número de Pallets", "Peso Total", "Número de SKUs", "Data de Criação"])
    df.to_csv(csv_file_path, index=False)  # Save the initial dataframe

# Section to add a new schedule
st.header("Adicionar Agendamento")

with st.form("add_schedule_form"):
    supplier_name = st.text_input("Indústria")
    invoice = st.text_input("Número da NF")
    dropoff_date = st.date_input("Data", min_value=datetime.date.today())
    dropoff_time = st.time_input("Horário")
    status = st.selectbox("Status", ["Agendado", "Completo", "Cancelado"])
    distribution_center = st.selectbox("Centro de Distribuição", ["CLAS", "GPA", "JSL"])
    load_type = st.selectbox("Tipo de Carga", ["Pallet Monoproduto", "Pallet Misto", "Estivado"])
    pallet_number = st.number_input("Número de Pallets", step=1)
    total_weight = st.number_input("Peso Total", step=1)
    sku_number = st.number_input("Número de SKUs", step=1)
    submitted = st.form_submit_button("Enviar")

# Define the maximum number of schedules allowed per day
max_schedules = {'CLAS': 10, 'JSL': 6, 'GPA': 7}

# Define the maximum number of simultaneous schedules
max_simulatenous = 2

# Minimum Time
minimum_time = {'CLAS': time(7, 0), 'JSL': time(13, 00), 'GPA': time(7, 0)}

# Maximum Time
maximum_time = {'CLAS': time(15, 0), 'JSL': time(20, 00), 'GPA': time(14, 0)}

if submitted:
    # Check how many schedules are already set for the selected drop-off date
    schedules_on_date = df[(df["Drop-off Date"] == str(dropoff_date)) &
                           (df["Centro de Distribuição"] == distribution_center)]
    if len(schedules_on_date) >= max_schedules[distribution_center]:
        st.error(
            f"Não é possível agendar mais de {max_schedules[distribution_center]} entregas para o dia {dropoff_date} por Centro de Distribuição.")
    elif dropoff_time < minimum_time[distribution_center] or dropoff_time > maximum_time[distribution_center]:
        st.error(
            f"É necessário agendar entre às {minimum_time[distribution_center]} e {maximum_time[distribution_center]}")
    else:
        if df.empty or df.ID.isnull().all():
            recent_schedule_id = 0
        else:
            recent_schedule_id = int(max(df.ID).split("-")[1])
        new_schedule = {
            "ID": f"SCHEDULE-{recent_schedule_id + 1}",
            "Indústria": supplier_name,
            "Número da NF": invoice,
            "Drop-off Date": dropoff_date,
            "Drop-off Time": dropoff_time.strftime("%H:%M"),
            "Status": status,
            "Centro de Distribuição": distribution_center,
            "Tipo de Carga": load_type,
            "Número de Pallets": pallet_number,
            "Peso Total": total_weight,
            "Número de SKUs": sku_number,
            "Data de Criação": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        insert_schedule(new_schedule)

        st.success("Agendamento enviado! Aqui estão os detalhes:")
        st.dataframe(pd.DataFrame([new_schedule]), use_container_width=True, hide_index=True)