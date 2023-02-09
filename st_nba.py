import streamlit as st
import plotly.express as px
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

def fix_dates(df):
    '''
    Pass in 'gamelog'. This will fix the dates and make them usable for plotting.
    '''
    ## fixing date column...
    df['DATE'] = df['DATE'].str[4:]

    ## append 2022 or 2023 to DATE
    months22 = ['Oct', 'Nov', 'Dec']

    date_df = df['DATE'].str.split(expand=True)
    date_df.rename(columns={0:'month',1:'day'}, inplace=True)
    date_df['year'] = np.where(date_df['month'].isin(months22), '2022', '2023')
    date_df['full'] = date_df['month'] + ' ' + date_df['day'] + ', ' + date_df['year']
    date_df['DATE'] = pd.to_datetime(date_df['full'])

    df['DATE'] = date_df['DATE']
    return df

st.set_page_config(page_title='PROPZ v2.4.0', page_icon=':basketball:', layout="wide", initial_sidebar_state="auto", menu_items=None)
st.write('<style>div.block-container{padding-top:0rem;}</style>', unsafe_allow_html=True)


## load the gamelog

gamelog = pd.read_csv('gamelog.csv')
gamelog = fix_dates(gamelog)
gamelog['HOME/AWAY'] = np.where(gamelog['OPP'].str.contains('@'), 'AWAY', 'HOME')

c1, c2 = st.columns(2)
with c1:
    pass
    st.write('Game log is current as of: {}'.format( gamelog['DATE'].max().strftime('%b %-d, %Y') ) )

st.markdown("<h1 style='text-align: center;'>NBA PROPZ 2.4.0</h1>", unsafe_allow_html=True)
hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')


## SIDEBAR / OPTIONS MENU
st.sidebar.markdown("## Options Menu")

## get unique teams
teams_list = gamelog['TEAM'].unique().tolist()
## team option
team_subset = st.sidebar.selectbox('Team', options=['Choose Team'] + teams_list)

## if a team is chosen, only show players from that team
if team_subset=='Choose Team':
    player_list = gamelog['NAME'].unique().tolist()
else:
    player_list = gamelog[gamelog['TEAM']==team_subset]['NAME'].unique().tolist()
## player option
player_subset = st.sidebar.selectbox('Player', options=['Choose Player'] + player_list)


def get_today_slate():
    url = 'https://www.espn.com/nba/lines'
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')
    parsed = soup.find_all('tr')

    names, records, mls = [], [], []
    for game in parsed:
        try:
            name = game.find_all('td')[0].get_text()
            record = game.find_all('td')[1].get_text()
            ml = game.find_all('td')[3].get_text()

            names.append(name)
            records.append(record)
            mls.append(ml)
        except: pass

    i=0
    home, away, homerec, awayrec, homeml, awayml = [], [], [], [], [], []
    for name, record, ml in zip(names, records, mls):
        i=i+1
        if i % 2 == 0:
            home.append(name)
            homerec.append(record)
            homeml.append(ml)
        else:
            away.append(name)
            awayrec.append(record)
            awayml.append(ml)

    return pd.DataFrame({'away':away,'home':home, 'awayrec':awayrec, 'homerec':homerec, 'awayml':awayml, 'homeml':homeml})

st.markdown("<h2 style='text-align: center;'>Today's Slate</h2>", unsafe_allow_html=True)
today = get_today_slate()
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("<h6 style='text-align: center;'>Home Team, Record (ATS) (ML Odds)", unsafe_allow_html=True)
with c2:
    st.markdown("<h6 style='text-align: center;'>@", unsafe_allow_html=True)
with c3:
    st.markdown("<h6 style='text-align: center;'>Away Team, Record (ATS) (ML Odds)", unsafe_allow_html=True)
for i, row in today.iterrows():
    with c1:
        st.markdown("<h6 style='text-align: center;'>{} {} ({})".format(row.away, row.awayrec, row.awayml), unsafe_allow_html=True)
    with c2:
        st.markdown("<h6 style='text-align: center;'>@", unsafe_allow_html=True)
    with c3:
        st.markdown("<h6 style='text-align: center;'>{} {} ({})".format(row.home, row.homerec, row.homeml), unsafe_allow_html=True)


## @TODO:
#st.header("Suggested Props for Today's Slate")
#st.write('Coming soon')

c1, _ = st.columns(2)
with c1:
    if player_subset!='Choose Player':
        plotbox = st.sidebar.selectbox(label='Show Plots', options=['All Stats','Points','Rebounds','Assists','Threes','Pts/Reb/Ast'])

## if any player is chosen, subset to only that player's trends
## x-axis Dates, y-axis is stat of choice
def gen_plotly(log, stat):
    '''
    Input: 'stat' is 'PTS','REB','AST','3PM','PRA'
    '''
    color_dict = {'PTS':'#E41A1C', 'REB':'#3773B8', 'AST':'#4DAF4A', '3PM':'#FF7F00','PRA':'#984EA3'}
    name_dict = {'PTS':'Points', 'REB':'Rebounds', 'AST':'Assists','3PM':'Threes','PRA':'Pts/Reb/Ast'}

    fig = px.line(x = log['DATE'], y = log[stat], title=player_subset, labels={'x':'Date','y':name_dict[stat]})
    fig['data'][0]['showlegend']=True
    fig['data'][0]['name']=name_dict[stat]
    fig['data'][0]['line']['color']=color_dict[stat]
    fig.update_layout(hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)

try:
    playerlog = gamelog[gamelog['NAME']==player_subset].sort_values(by='DATE')
    if plotbox=='All Stats':
        fig = px.line(x = playerlog['DATE'], y = playerlog['PTS'], title=player_subset,labels={'x':'Date', 'y':''})
        fig['data'][0]['showlegend']=True
        fig['data'][0]['name']='Points'
        fig['data'][0]['line']['color']='#E41A1C'
        fig.add_scatter(x = playerlog['DATE'], y = playerlog['REB'], name='Rebounds', line_color='#3773B8')
        fig.add_scatter(x = playerlog['DATE'], y = playerlog['AST'], name='Assists', line_color='#4DAF4A')
        fig.add_scatter(x = playerlog['DATE'], y = playerlog['3PM'], name='Threes', line_color='#FF7F00')
        fig.add_scatter(x = playerlog['DATE'], y = playerlog['PRA'], name='PRA', line_color='#984EA3')
        fig.update_layout(hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)
    if plotbox=='Points': gen_plotly(playerlog, 'PTS')
    if plotbox=='Rebounds': gen_plotly(playerlog, 'REB')
    if plotbox=='Assists': gen_plotly(playerlog, 'AST')
    if plotbox=='Threes': gen_plotly(playerlog, '3PM')
    if plotbox=='Pts/Reb/Ast': gen_plotly(playerlog, 'PRA')
except: pass


## prop sliders
thres_pts = st.sidebar.number_input('Points', value=19.5, step=1.0, help='Adjust threshold for points to compare prop trends.')
thres_reb = st.sidebar.number_input('Rebounds', value=5.5, step=1.0, help='Adjust threshold for rebounds to compare prop trends.')
thres_ast = st.sidebar.number_input('Assists', value=3.5, step=1.0, help='Adjust threshold for assists to compare prop trends.')
thres_3pm = st.sidebar.number_input('Threes', value=1.5, step=1.0, help='Adjust threshold for threes to compare prop trends.')
thres_pra = st.sidebar.number_input('Pts/Reb/Ast', value=24.5, step=1.0, help='Adjust threshold for PRA to compare prop trends.')

## Print trends
if player_subset!= 'Choose Player:':
    st.header('{} has hit...'.format(player_subset))
    c1,c2,c3 = st.columns(3)
    with c1:
        st.subheader('...in all games:')
        l5 = gamelog[gamelog['NAME']==player_subset].head(5)
        l10 = gamelog[gamelog['NAME']==player_subset].head(10)
        l25 = gamelog[gamelog['NAME']==player_subset].head(25)

        st.write('...over {} points in {}/5, {}/10, and {}/25'.format(thres_pts, sum(l5['PTS'] >= thres_pts), sum(l10['PTS'] >= thres_pts), sum(l25['PTS'] >= thres_pts) ) )
        st.write('...over {} rebounds in {}/5, {}/10, and {}/25'.format(thres_reb, sum(l5['REB'] >= thres_reb), sum(l10['REB'] >= thres_reb), sum(l25['REB'] >= thres_reb) ) )
        st.write('...over {} assists in {}/5, {}/10, and {}/25'.format(thres_ast, sum(l5['AST'] >= thres_ast), sum(l10['AST'] >= thres_ast), sum(l25['AST'] >= thres_ast) ) )
        st.write('...over {} threes in {}/5, {}/10, and {}/25'.format(thres_3pm, sum(l5['3PM'] >= thres_3pm), sum(l10['3PM'] >= thres_3pm), sum(l25['3PM'] >= thres_3pm) ) )
        st.write('...over {} PRA in {}/5, {}/10, and {}/25'.format(thres_pra, sum(l5['PRA'] >= thres_pra), sum(l10['PRA'] >= thres_pra), sum(l25['PRA'] >= thres_pra) ) )
    with c2:
        st.subheader('...at home:')
        gamelog_home = gamelog[gamelog['HOME/AWAY']=='HOME']
        l5 = gamelog_home[gamelog_home['NAME']==player_subset].head(5)
        l10 = gamelog_home[gamelog_home['NAME']==player_subset].head(10)
        l25 = gamelog_home[gamelog_home['NAME']==player_subset].head(25)

        st.write('...over {} points in {}/5, {}/10, and {}/25'.format(thres_pts, sum(l5['PTS'] >= thres_pts), sum(l10['PTS'] >= thres_pts), sum(l25['PTS'] >= thres_pts) ) )
        st.write('...over {} rebounds in {}/5, {}/10, and {}/25'.format(thres_reb, sum(l5['REB'] >= thres_reb), sum(l10['REB'] >= thres_reb), sum(l25['REB'] >= thres_reb) ) )
        st.write('...over {} assists in {}/5, {}/10, and {}/25'.format(thres_ast, sum(l5['AST'] >= thres_ast), sum(l10['AST'] >= thres_ast), sum(l25['AST'] >= thres_ast) ) )
        st.write('...over {} threes in {}/5, {}/10, and {}/25'.format(thres_3pm, sum(l5['3PM'] >= thres_3pm), sum(l10['3PM'] >= thres_3pm), sum(l25['3PM'] >= thres_3pm) ) )
        st.write('...over {} PRA in {}/5, {}/10, and {}/25'.format(thres_pra, sum(l5['PRA'] >= thres_pra), sum(l10['PRA'] >= thres_pra), sum(l25['PRA'] >= thres_pra) ) )
    with c3:
        st.subheader('...on the road:')
        gamelog_away = gamelog[gamelog['HOME/AWAY']=='AWAY']
        l5 = gamelog_away[gamelog_away['NAME']==player_subset].head(5)
        l10 = gamelog_away[gamelog_away['NAME']==player_subset].head(10)
        l25 = gamelog_away[gamelog_away['NAME']==player_subset].head(25)

        st.write('...over {} points in {}/5, {}/10, and {}/25'.format(thres_pts, sum(l5['PTS'] >= thres_pts), sum(l10['PTS'] >= thres_pts), sum(l25['PTS'] >= thres_pts) ) )
        st.write('...over {} rebounds in {}/5, {}/10, and {}/25'.format(thres_reb, sum(l5['REB'] >= thres_reb), sum(l10['REB'] >= thres_reb), sum(l25['REB'] >= thres_reb) ) )
        st.write('...over {} assists in {}/5, {}/10, and {}/25'.format(thres_ast, sum(l5['AST'] >= thres_ast), sum(l10['AST'] >= thres_ast), sum(l25['AST'] >= thres_ast) ) )
        st.write('...over {} threes in {}/5, {}/10, and {}/25'.format(thres_3pm, sum(l5['3PM'] >= thres_3pm), sum(l10['3PM'] >= thres_3pm), sum(l25['3PM'] >= thres_3pm) ) )
        st.write('...over {} PRA in {}/5, {}/10, and {}/25'.format(thres_pra, sum(l5['PRA'] >= thres_pra), sum(l10['PRA'] >= thres_pra), sum(l25['PRA'] >= thres_pra) ) )




## Associated detailed data / descriptions
st.header('Full Game Log for Chosen Player')
st.write('If a player is chosen with the filter menu on the left, it will show the game log of that player. Otherwise, it will show the full game log for all possible players and teams.')

## Consider all cases for displaying data
## Do not choose team or player -> show full log
if (team_subset=='Choose Team') & (player_subset=='Choose Player'):
    st.dataframe(gamelog)
## Choose team but not a player -> show log for all players on chosen team
elif (team_subset!='Choose Team') & (player_subset=='Choose Player'):
    st.dataframe(gamelog[gamelog.TEAM==team_subset].reset_index(drop=True))
## Choose player -> show log for chosen player
elif player_subset!='Choose Player':
    st.dataframe(gamelog[gamelog.NAME==player_subset].reset_index(drop=True))

## Button for downloading gamelog data to CSV
gamelog_csv = convert_df(gamelog)
st.download_button("Download CSV of full game log for all players", gamelog_csv, "gamelog.csv", "text/csv", key='download-csv')