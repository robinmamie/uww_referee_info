import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

import sys


def get_ref_count(df, category, sex):
    df_tmp = df[((df['category'] == category) & (df['sex'] == sex))].groupby(df["birthdate"].dt.year).count()
    return df_tmp.reindex(range(min(df.birthdate).year, max(df.birthdate).year+1), fill_value=0)


def graph_data():
    df_int = pd.read_csv('int_referees.csv')
    df_int['birthdate'] = pd.to_datetime(df_int['birthdate'])

    colors = {
        'RCM': ['black', 'lightgray'],
        'IS': ['gold', 'yellow'],
        'I': ['r', 'pink'],
        'II': ['g', 'lightgreen'],
        'III': ['b', 'lightblue'],
    }
    for category in colors:
        df_tmp_m = get_ref_count(df_int, category, 'M')
        df_tmp_f = get_ref_count(df_int, category, 'F')
        df_tmp = pd.DataFrame({f"Female ({df_tmp_f['name'].sum()})": df_tmp_f['name'], f"Male ({df_tmp_m['name'].sum()})": df_tmp_m['name']})

        ax = df_tmp.plot(kind="bar", stacked=True, color=colors[category], figsize=(10,3))
        nb_ref_cat =  df_int[df_int['category'] == category]['name'].count()
        ax.set_title(f"UWW {category} ({nb_ref_cat} referees)\nsplit by gender")
        ax.set_xlabel("Birthyear")
        ax.set_ylabel("Number of referees\nby birthyear")
        ax.set_ylim(0, 35)
        ax.grid(axis='y')
        plt.savefig(f'img/stats_{category}.png', dpi=300, bbox_inches='tight')


def main():
    graph_data()


if __name__ == '__main__':
    sys.exit(main())
