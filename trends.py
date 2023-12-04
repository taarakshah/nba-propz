import streamlit as st
import utils


def displayPlayerTrends(gamelog, player_subset, thres_pts, thres_reb, thres_ast, thres_3pm, thres_pra):
	## Print trends
	if player_subset != 'Choose Player':
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
					
			st.subheader('Prop Math for {}'.format(player_subset))
			st.write('This section rounds down to the nearest prop threshold and does the calculations for often a player has hit at that threshold')
			c1, c2, c3 = st.columns(3)
			# points base is 10, highest is 40, goes up by 5s
			ptsProp = max(10, utils.roundDownToNearest(thres_pts, 5)) - 0.5
			# rebs base is 2, highest is 18, goes up by 2s
			rebProp = max(2, utils.roundDownToNearest(thres_reb, 2)) - 0.5
			# asts base is 2, highest is 12, goes up by 2s
			astProp = max(2, utils.roundDownToNearest(thres_ast, 2)) - 0.5
			# 3pm base is 1, highest is 7, goes up by 1s
			threesProp = max(1, utils.roundDownToNearest(thres_3pm, 1)) - 0.5
			# pra base is 15, highest is 50, goes up by 5s
			praProp = max(15, utils.roundDownToNearest(thres_pra, 5)) - 0.5

			st.write('Thresholds: {}+ Points, {}+ Rebounds, {}+ Assists, {}+ Threes, {}+ PRA'.format(int(ptsProp + 0.5), int(rebProp + 0.5), int(astProp + 0.5), int(threesProp + 0.5), int(praProp + 0.5)))
			
			with c1:
				st.subheader('...in all games:')
				l5 = gamelog[gamelog['NAME']==player_subset].head(5)
				l10 = gamelog[gamelog['NAME']==player_subset].head(10)
				l25 = gamelog[gamelog['NAME']==player_subset].head(25)

				st.write('...over {} points in {}/5, {}/10, and {}/25'.format(ptsProp, sum(l5['PTS'] >= ptsProp), sum(l10['PTS'] >= ptsProp), sum(l25['PTS'] >= ptsProp) ) )
				st.write('...over {} rebounds in {}/5, {}/10, and {}/25'.format(rebProp, sum(l5['REB'] >= rebProp), sum(l10['REB'] >= rebProp), sum(l25['REB'] >= rebProp) ) )
				st.write('...over {} assists in {}/5, {}/10, and {}/25'.format(astProp, sum(l5['AST'] >= astProp), sum(l10['AST'] >= astProp), sum(l25['AST'] >= astProp) ) )
				st.write('...over {} threes in {}/5, {}/10, and {}/25'.format(threesProp, sum(l5['3PM'] >= threesProp), sum(l10['3PM'] >= threesProp), sum(l25['3PM'] >= threesProp) ) )
				st.write('...over {} PRA in {}/5, {}/10, and {}/25'.format(praProp, sum(l5['PRA'] >= praProp), sum(l10['PRA'] >= praProp), sum(l25['PRA'] >= praProp) ) )
			with c2:
				st.subheader('...at home:')
				gamelog_home = gamelog[gamelog['HOME/AWAY']=='HOME']
				l5 = gamelog_home[gamelog_home['NAME']==player_subset].head(5)
				l10 = gamelog_home[gamelog_home['NAME']==player_subset].head(10)
				l25 = gamelog_home[gamelog_home['NAME']==player_subset].head(25)

				st.write('...over {} points in {}/5, {}/10, and {}/25'.format(ptsProp, sum(l5['PTS'] >= ptsProp), sum(l10['PTS'] >= ptsProp), sum(l25['PTS'] >= ptsProp) ) )
				st.write('...over {} rebounds in {}/5, {}/10, and {}/25'.format(rebProp, sum(l5['REB'] >= rebProp), sum(l10['REB'] >= rebProp), sum(l25['REB'] >= rebProp) ) )
				st.write('...over {} assists in {}/5, {}/10, and {}/25'.format(astProp, sum(l5['AST'] >= astProp), sum(l10['AST'] >= astProp), sum(l25['AST'] >= astProp) ) )
				st.write('...over {} threes in {}/5, {}/10, and {}/25'.format(threesProp, sum(l5['3PM'] >= threesProp), sum(l10['3PM'] >= threesProp), sum(l25['3PM'] >= threesProp) ) )
				st.write('...over {} PRA in {}/5, {}/10, and {}/25'.format(praProp, sum(l5['PRA'] >= praProp), sum(l10['PRA'] >= praProp), sum(l25['PRA'] >= praProp) ) )
			with c3:
				st.subheader('...on the road:')
				gamelog_away = gamelog[gamelog['HOME/AWAY']=='AWAY']
				l5 = gamelog_away[gamelog_away['NAME']==player_subset].head(5)
				l10 = gamelog_away[gamelog_away['NAME']==player_subset].head(10)
				l25 = gamelog_away[gamelog_away['NAME']==player_subset].head(25)

				st.write('...over {} points in {}/5, {}/10, and {}/25'.format(ptsProp, sum(l5['PTS'] >= ptsProp), sum(l10['PTS'] >= ptsProp), sum(l25['PTS'] >= ptsProp) ) )
				st.write('...over {} rebounds in {}/5, {}/10, and {}/25'.format(rebProp, sum(l5['REB'] >= rebProp), sum(l10['REB'] >= rebProp), sum(l25['REB'] >= rebProp) ) )
				st.write('...over {} assists in {}/5, {}/10, and {}/25'.format(astProp, sum(l5['AST'] >= astProp), sum(l10['AST'] >= astProp), sum(l25['AST'] >= astProp) ) )
				st.write('...over {} threes in {}/5, {}/10, and {}/25'.format(threesProp, sum(l5['3PM'] >= threesProp), sum(l10['3PM'] >= threesProp), sum(l25['3PM'] >= threesProp) ) )
				st.write('...over {} PRA in {}/5, {}/10, and {}/25'.format(praProp, sum(l5['PRA'] >= praProp), sum(l10['PRA'] >= praProp), sum(l25['PRA'] >= praProp) ) )