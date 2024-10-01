import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from pyngrok import ngrok

# Load Data
dataframes = {
    "Aotizhongxin": pd.read_csv("data/PRSA_Data_Aotizhongxin_20130301-20170228.csv"),
    "Changping": pd.read_csv("data/PRSA_Data_Changping_20130301-20170228.csv"),
    "Dingling": pd.read_csv("data/PRSA_Data_Dingling_20130301-20170228.csv"),
    "Dongsi": pd.read_csv("data/PRSA_Data_Dongsi_20130301-20170228.csv"),
    "Guanyuan": pd.read_csv("data/PRSA_Data_Guanyuan_20130301-20170228.csv"),
    "Gucheng": pd.read_csv("data/PRSA_Data_Gucheng_20130301-20170228.csv"),
    "Huairou": pd.read_csv("data/PRSA_Data_Huairou_20130301-20170228.csv"),
    "Nongzhanguan": pd.read_csv("data/PRSA_Data_Nongzhanguan_20130301-20170228.csv"),
    "Shunyi": pd.read_csv("data/PRSA_Data_Shunyi_20130301-20170228.csv"),
    "Tiantan": pd.read_csv("data/PRSA_Data_Tiantan_20130301-20170228.csv"),
    "Wanliu": pd.read_csv("data/PRSA_Data_Wanliu_20130301-20170228.csv"),
    "Wanshouxigong": pd.read_csv("data/PRSA_Data_Wanshouxigong_20130301-20170228.csv"),
}

# Fungsi untuk menghitung AQI
def calculate_ispu(pm25):
    if 0 <= pm25 <= 35:
        return 0 + ((50 - 0) / (35 - 0)) * (pm25 - 0)
    elif 35.1 <= pm25 <= 75:
        return 51 + ((100 - 51) / (75 - 35.1)) * (pm25 - 35.1)
    elif 75.1 <= pm25 <= 115:
        return 101 + ((150 - 101) / (115 - 75.1)) * (pm25 - 75.1 )
    elif 115.1 <= pm25 <= 150:
        return 151 + ((200 - 151) / (150 - 115.1)) * (pm25 - 115.1)
    elif 150.1 <= pm25 <= 250:
        return 201 + ((300 - 201) / (250 - 150.1)) * (pm25 - 150.1)
    else:
        return 301

# Judul Dashboard
st.title('Dashboard Data Suhu dan Kualitas Udara Sekitar Beijing')

# Dropdown untuk memilih DataFrame
selected_location = st.selectbox('Pilih Lokasi:', list(dataframes.keys()))
selected_df = dataframes[selected_location]

# Konversi tahun, bulan, hari menjadi datetime
selected_df['date'] = pd.to_datetime(selected_df[['year', 'month', 'day']])
last_date = selected_df['date'].max()
one_month_ago = last_date - pd.DateOffset(months=1)
last_month_data = selected_df[selected_df['date'] >= one_month_ago]

# Hitung rata-rata, maksimum, dan minimum suhu harian
daily_avg_TEMP = last_month_data.groupby(last_month_data['date'].dt.date).agg({
    "TEMP": ["mean", "max", "min"]
}).reset_index()

# Tampilkan data dalam tabel
st.subheader(f'Data Suhu Bulan Lalu di {selected_location}')
st.write(daily_avg_TEMP)

avg_temp = daily_avg_TEMP[('TEMP', 'mean')].mean()
st.metric(label="Suhu Rata-Rata (°C)", value=f"{avg_temp:.2f}")

# Plotting Suhu
plt.figure(figsize=(10, 5))
sns.lineplot(data=daily_avg_TEMP, x='date', y=('TEMP', 'mean'), label='Rata-Rata Suhu', color='blue')
sns.lineplot(data=daily_avg_TEMP, x='date', y=('TEMP', 'max'), label='Suhu Maksimum', color='red')
sns.lineplot(data=daily_avg_TEMP, x='date', y=('TEMP', 'min'), label='Suhu Minimum', color='green')
plt.title(f'Rata-Rata, Maksimum, dan Minimum Suhu Harian di {selected_location}')
plt.xlabel('Tanggal')
plt.ylabel('Suhu (°C)')
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()

# Tampilkan plot di Streamlit
st.pyplot(plt)

# Menambahkan perhitungan rata-rata bulanan polutan untuk setiap daerah
# Membuat bulan dan mengambil data selama setahun terakhir
selected_df['bulan'] = pd.to_datetime(selected_df[['year', 'month']].assign(day=1))
last_month = selected_df['bulan'].max()
one_year_ago = last_month - pd.DateOffset(years=1)
last_year_data = selected_df[selected_df['bulan'] >= one_year_ago]

# Hitung rata-rata bulanan polutan
monthly_avg_pollutant = last_year_data.groupby(last_year_data['bulan'].dt.to_period('M')).agg({
    "PM2.5": "mean",
    "PM10": "mean",
    "SO2": "mean",
    "NO2": "mean",
    "CO": "mean",
    "O3": "mean"
}).reset_index()

# Tampilkan data polutan bulanan
st.subheader(f'Rata-Rata Bulanan Polutan di {selected_location}')
st.write(monthly_avg_pollutant)

# Tambahkan kode untuk menghitung AQI
bins = [0, 50, 100, 150, 200, 300, float('inf')]
kategori = ['Baik', 'Sedang', 'Tidak sehat untuk orang sensitif', 'Tidak Sehat', 'Sangat Tidak Sehat', 'Berbahaya']

# Menghitung AQI
monthly_avg_pollutant['AQI'] = monthly_avg_pollutant['PM2.5'].apply(calculate_ispu)
monthly_avg_pollutant['Kategori_AQI'] = pd.cut(monthly_avg_pollutant['AQI'], bins=bins, labels=kategori, right=False, include_lowest=True, duplicates='drop')

# Tampilkan data AQI
st.subheader(f'AQI Bulanan di {selected_location}')
st.write(monthly_avg_pollutant[['bulan', 'PM2.5', 'AQI', 'Kategori_AQI']])

# Plotting AQI
color_mapping = {
    'Baik': 'green',
    'Sedang': 'yellow',
    'Tidak sehat untuk orang sensitif': 'orange',
    'Tidak Sehat': 'red',
    'Sangat Tidak Sehat': 'darkred',
    'Berbahaya': 'black'
}

st.subheader("Kategori AQI dan Warna")
legend_labels = ['Baik', 'Sedang', 'Tidak sehat untuk orang sensitif', 'Tidak Sehat', 'Sangat Tidak Sehat', 'Berbahaya']
legend_colors = ['green', 'yellow', 'orange', 'red', 'darkred', 'black']

legend_patches = [mpatches.Patch(color=color, label=label) for label, color in color_mapping.items()]
plt.legend(handles=legend_patches,
           bbox_to_anchor=(1.05, 1), loc='upper left', prop={'size': 8})

colors = [color_mapping[kategori] for kategori in monthly_avg_pollutant['Kategori_AQI']]
plt.figure(figsize=(10, 5))
plt.bar(x=monthly_avg_pollutant['bulan'].astype(str), height=monthly_avg_pollutant['AQI'], width=0.5, color=colors)
plt.xlabel("Bulan")
plt.ylabel("AQI")
plt.title(f"Grafik AQI Bulanan di {selected_location}")
plt.xticks(rotation=45)
plt.tight_layout()

# Tampilkan plot AQI di Streamlit
st.pyplot(plt)
