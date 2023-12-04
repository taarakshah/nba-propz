import streamlit as st
import utils

def displayGameLog(gamelog, team_subset, player_subset):
	## Associated detailed data / descriptions
	st.header('Full Game Log for Chosen Player')
	st.write('If a player is chosen with the filter menu on the left, it will show the game log of that player. Otherwise, it will show the full game log for all possible players and teams.')
	st.write('Game log is current as of: {}'.format( gamelog['DATE'].max().strftime('%b %d, %Y') ) )
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
	gamelog_csv = utils.convert_df(gamelog)
	st.download_button("Download CSV of full game log for all players", gamelog_csv, "gamelog.csv", "text/csv", key='download-csv')