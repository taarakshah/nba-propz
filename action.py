import streamlit as st
import numpy as np
import pandas as pd
import json
import requests
from bs4 import BeautifulSoup

def action_scrape(sport=None, propnames=None):
    fulldf = pd.DataFrame()
    ## need header for access to site
    headers = { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 \ (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    for propname in propnames:
        urlbuild = 'https://www.actionnetwork.com/'+sport+'/props/'
        url = urlbuild + propname
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.content, 'html.parser')
        ## get json
        parsed = soup.find_all('script')
        jstext = parsed[-1].string
        ## load entire json into pandas, drop unnecessary columns
        data = json.loads(jstext)
        #print( json.dumps(data, indent=2) )
        df_js = pd.json_normalize(data)

        ## get o/u corresponding value -- smaller corresponds to over, larger corresponds to under according to nba
        ## checker:
        #print(df_js.filter(regex='props.pageProps.initialMarketConfig.market.rules.options'))
        cols = df_js.filter(regex='props.pageProps.initialMarketConfig.market.rules.options').columns.tolist()
        ## remove prefix string, keep only the number, and save it to unique list to avoid dupes
        try:
            nums = []
            for i in range(len(cols)):
                nums.append(int(cols[i].replace('props.pageProps.initialMarketConfig.market.rules.options.', '')[0:2].replace('.','')))
                nums = np.unique(nums).tolist()
        except: pass

        ## get name of prop page
        stat = df_js['props.pageProps.SEOData.header'].values[0]

        ## keep relevant columns now that we have o/u numbers, expand the json
        keep = 'props.pageProps.initialMarketConfig.market.'
        cols_to_keep = [keep+'books',keep+'teams',keep+'players']

        ## check if the cols_to_keep index is in the df_js, if not, then return null
        if (cols_to_keep[0] not in df_js.columns) | (cols_to_keep[1] not in df_js.columns) | (cols_to_keep[2] not in df_js.columns):
            return None

        df = df_js[cols_to_keep]
        df = df.copy()
        df.rename(columns={cols_to_keep[0]:'books', cols_to_keep[1]:'teams', cols_to_keep[2]:'players'}, inplace=True)

        ## create odds df
        odds = pd.json_normalize(df['books'][0], record_path='odds', meta='book_id')
        odds = odds[odds.columns.drop(list(odds.filter(regex='deeplink')))]
        # create o/u to be obvious -- its hidden in option type id -- smaller num corresponds to over, larger to under
        try:
            odds['ou'] = np.where(odds['option_type_id']==np.min(nums), 'over', 'under')
        except: pass

        ## get book names
        book_ids = odds.book_id.unique()
        bookdict= {}
        for i in book_ids:
            try:
                book = df_js['props.pageProps.bookMap.{}.display_name'.format(i)].values[0]
                if i not in bookdict:
                    bookdict[i] = book
            except: pass
        ## exception for other book id
        bookdict[15] = 'Best Odds'

        teams = pd.json_normalize(df['teams'][0])
        players = pd.json_normalize(df['players'][0])
        books = pd.DataFrame(bookdict.items(), columns=['book_id', 'book_name'])

        odds1 = odds.merge(books, on='book_id')
        odds2 = odds1.merge(teams[['id','display_name']], left_on='team_id', right_on='id')
        odds3 = odds2.merge(players[['id','full_name']], left_on='player_id', right_on='id')
        df = odds3[odds3.columns.drop(list(odds.filter(regex='id')))]
        df = df.drop(['id_x','id_y'], axis=1)
        df['prop'] = propname
        df = df.sort_values(by=['prop','full_name','book_name','is_best'], ascending=[True,True,True,False])
        fulldf = pd.concat([fulldf, df], ignore_index=True)
    return fulldf

def displayActionNetworkSection(thres, team_subset, player_subset, team_dict):
	## get action data for NBA props
	nba_propnames = ['points', 'rebounds', 'assists', '3fgm', 'points-rebounds-assists']
	name_dict = {'points':''}
	action = action_scrape(sport='nba', propnames=nba_propnames)


	if action is None:
			st.write('No data found for NBA props. Please check back later.')
			return
	
	action_display = action[['edge','prop','ou','value','money','full_name','display_name','grade','implied_value','projected_value','bet_quality','book_name',]]

	st.subheader('Action Edge Data')

	c1, c2 = st.columns(2)
	with c1:
			st.write('Below is data from Action Network on player edges and lines across books. Choose your book, or "all", to update the data. Choosing a specific team or player will also update the data to only show that team or player. If a team is not playing today, the data will come up empty. Click on a column to sort by that column.')
	with c2:
			book_opt = st.selectbox('Select Book', options=['All'] + action['book_name'].unique().tolist()[1:])

	### cases to display
	## set thresholds, update them if certain player is chosen in action data

	## all books, all teams, all players
	if (book_opt=='All') & (team_subset=='Choose Team') & (player_subset=='Choose Player'):
			## all books, all teams, all players
			st.dataframe(action_display)
	## all books, certain team, all players
	elif (book_opt=='All') & (team_subset!='Choose Team') & (player_subset=='Choose Player'):
			st.dataframe(action_display[action_display['display_name']==team_dict[team_subset]])
	## all books, certain player ################################################################## UPDATES THRESHOLDS
	elif (book_opt=='All') & (player_subset!='Choose Player'):
			temp = action_display[action_display['full_name']==player_subset]
			st.dataframe(temp)

			try:
					thres['pts'] = temp[temp['prop']=='points']['value'].values[0]
					thres['reb'] = temp[temp['prop']=='rebounds']['value'].values[0]
					thres['ast'] = temp[temp['prop']=='assists']['value'].values[0]
					thres['3pm'] = temp[temp['prop']=='3fgm']['value'].values[0]
					thres['pra'] = temp[temp['prop']=='points-rebounds-assists']['value'].values[0]
			except: pass
	## certain book, all teams, all players
	elif (book_opt!='All') & (team_subset=='Choose Team') & (player_subset=='Choose Player'):
			st.dataframe(action_display[action_display['book_name']==book_opt])
	## certain book, certain team, all players
	elif (book_opt!='All') & (team_subset!='Choose Team') & (player_subset=='Choose Player'):
			st.dataframe(action_display[ (action_display['book_name']==book_opt) & (action_display['display_name']==team_dict[team_subset])])
	## certain book, certain player ############################################################## UPDATES THRESHOLDS
	elif (book_opt!='All') & (player_subset!='Choose Player'):
			temp = action_display[ (action_display['book_name']==book_opt) & (action_display['full_name']==player_subset) ]
			st.dataframe(temp)

			try:
					thres['pts'] = temp[temp['prop']=='points']['value'].values[0]
					thres['reb'] = temp[temp['prop']=='rebounds']['value'].values[0]
					thres['ast'] = temp[temp['prop']=='assists']['value'].values[0]
					thres['3pm'] = temp[temp['prop']=='3fgm']['value'].values[0]
					thres['pra'] = temp[temp['prop']=='points-rebounds-assists']['value'].values[0]
			except: pass
	else:
			st.write('What fuckin option combo is this? Anyway, something is wrong, here is the full data.')
			st.dataframe(action_display)
	