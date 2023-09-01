
import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd
import altair as alt
import numpy as np


st.write("Psss, come here I've heard you want to buy some wine ... ")

st.title ("Wine Genie - Beta")

#st.header("this is the markdown")
#st.markdown("this is the header")
#st.subheader("this is the subheader")
#st.caption("this is the caption")


# load the dataframe 

@st.cache_data
def get_data():
    #AWS_BUCKET_URL = "https://streamlit-demo-data.s3-us-west-2.amazonaws.com"
    df = pd.read_csv("wine_diplo_2023_28Aug.csv")
    return df
    #return df.set_index("country")


df = get_data()


#make sure the price and rating are floats 

#remove commas in the price and - in vivino rating
df['price_usd'] = df['price_usd'].replace({',': ''}, regex=True)
df['vivino_rating'] = df['vivino_rating'].replace({'-': '0'}, regex=True)

df['price_usd'] = df['price_usd'].astype(float) #(or int)
df['vivino_rating'] = df['vivino_rating'].astype(float) #(or int)


#round price and vivino rating

df['price_usd']=df['price_usd'].round(2)
df['vivino_rating']=df['vivino_rating'].round(2)



#keep only where we have vivino ratings
df=df[df['vivino_rating']>0]

# choose countries

#choose the countries
countries = st.multiselect(
    "Choose countries", list(df.country.unique())
)

#refine dataset
#data = df.loc[countries]
if len(countries)>0:
	data=df[df['country'].isin(countries)]
else:
	data=df

#choose the regions

regions = st.multiselect(
    "Choose regions", list(data.vivino_region.unique())
)

if len(regions)>0:
	data=data[data['vivino_region'].isin(regions)]

#choose the price range 
values = st.slider(
    'Choose the price range',
    0, 500, (0, 500))

#confidence filter
min_confidence=st.slider('define mininum confidence', 0, 100, 75)
#filter confidence  

data=data[data['confidence']>min_confidence]

#data=data[data['price_usd'].isin(values)]

data=data[data['price_usd'].between(*values)]

#choose a wine directly

wine = st.multiselect(
    "Choose a wine:", list(data.Name.unique())
)

if len(wine)>0:
	data=data[data['Name'].isin(wine)]

# Search by keyword

data['name_lower']=data['Name'].str.lower()
keyword = st.text_input('Or search a keyword', value="")

if len(keyword)>0:
	data=data[data['name_lower'].str.contains(keyword.lower())]


#sort by price asc
data=data.sort_values(by='price_usd', ascending=True)

# fit a log regression on the rating vs price
fit = np.polyfit(np.log(list(data['price_usd'])), list(data['vivino_rating']) , 1)

# calculate deviation vs fit in absolute and relatvie 
data['log_fit_delta']=data['vivino_rating']-(fit[1] + fit[0] * np.log(data['price_usd']))
data['log_fit_delta_relative']=data['log_fit_delta'] / (fit[1] + fit[0] * np.log(data['price_usd']))


# color coding = relative delta vs log fit

chart_no_color = (
   alt.Chart(data).mark_circle().encode(   
   	x = alt.Y('price_usd' , scale=alt.Scale(type='log',domain=[data['price_usd'].min(), data['price_usd'].max()])),
   	y = alt.Y('vivino_rating' , scale=alt.Scale(domain=[data['vivino_rating'].min(), data['vivino_rating'].max()])),
   	tooltip=['price_usd','vivino_rating','Name','confidence',]
   	#'IDS link','vivino_url'],

   	))

chart_color = (
   alt.Chart(data).mark_circle().encode(   
   	x = alt.Y('price_usd' , scale=alt.Scale(type='log',domain=[data['price_usd'].min(), data['price_usd'].max()])),
   	y = alt.Y('vivino_rating' , scale=alt.Scale(domain=[data['vivino_rating'].min(), data['vivino_rating'].max()])),
   	#y='vivino_rating' , 
   	color=alt.Color('log_fit_delta_relative',legend=None).scale(scheme='redyellowgreen'),
   	tooltip=['price_usd','vivino_rating','Name','confidence','log_fit_delta_relative']
   	#'IDS link','vivino_url'],

   	)
    )
   


chart=chart_color + chart_no_color.transform_regression('price_usd', 'vivino_rating', method='log').mark_line()
st.altair_chart(chart, use_container_width=True)

# order the dataset by delta relative and keep only top 10
data_top=data.sort_values('log_fit_delta_relative', ascending=False)
data_top=data_top[['Name','country','vivino_region','price_usd','vivino_rating','IDS link','vivino_url','confidence']]
data_top=data_top.head(100)


st.header("top 100 wines based on your criterias")

# define color coding for the confidence column

def color_confidence(val):
    color = 'red' if val<=65 else 'orange' if val<=85 else 'green'
    return f'background-color: {color}'


#st.dataframe(data_top.reset_index(drop=True).style.applymap(color_column, subset=['vivino_rating']))

def make_clickable_buy(link):
    return f'<a target="_blank" href="{link}">"Buy Now"</a>'

def make_clickable_vivino(link):
    return f'<a target="_blank" href="{link}">"Check it on Vivino"</a>'

data_top['IDS link'] = df['IDS link'].apply(make_clickable_buy)
data_top['vivino_url'] = df['vivino_url'].apply(make_clickable_vivino)

data_top=data_top.style\
	.applymap(color_confidence, subset=['confidence'])\
	.format({"price_usd": "{:.1f}","vivino_rating": "{:.1f}"})
	#.format({"vivino_rating": "{:.1f}"})


data_top = data_top.to_html(escape=False)
st.write(data_top, unsafe_allow_html=True)

#st.dataframe(data_top.style\
#	.background_gradient(axis=None, cmap='RdYlGn_r',subset=['price_usd'])
#	.background_gradient(axis=None, cmap='RdYlGn',subset=['vivino_rating'])
#	)


st.caption("\
	\
	Credit: Hugo Ruiz Verastegui - hugo.ruiz.verastegui@gmail.com ")



