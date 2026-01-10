import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

import sys


def get_ref_count(df_orig, df, sex):
    df_tmp = df[(df['sex'] == sex)].groupby(df["birthdate"].dt.year).count()
    return df_tmp.reindex(range(min(df_orig.birthdate).year, max(df_orig.birthdate).year+1), fill_value=0)


def graph_data():
    colors = {
        'IS': ['gold', 'yellow', 'lightgray'],
        'I': ['r', 'pink', 'lightgray'],
        'II': ['g', 'lightgreen', 'lightgray'],
        'III': ['b', 'lightblue', 'lightgray'],
    }
    df_uww_all = pd.read_csv('uww_referees.csv')
    df_uww_all['birthdate'] = pd.to_datetime(df_uww_all['birthdate'])
    df_uww_all = df_uww_all.loc[df_uww_all['category'].isin(list(colors.keys()) + ['IS-RCM'])]

    for category in colors:
        df_cat = df_uww_all[((df_uww_all['category'] == category) | (df_uww_all['category'] == f"{category}-RCM"))]
        df_tmp_m = get_ref_count(df_uww_all, df_cat, 'M')
        df_tmp_f = get_ref_count(df_uww_all, df_cat, 'F')

        nb_ref_cat_all =  df_cat['name'].count()

        df_tmp = pd.DataFrame({
            f"Female ({df_tmp_f['name'].sum()})": df_tmp_f['name'],
            f"Male ({df_tmp_m['name'].sum()})": df_tmp_m['name'],
        })

        ax = df_tmp.plot(kind="bar", stacked=True, color=colors[category], figsize=(10,4))
        ax.set_title(f"UWW {category} ({nb_ref_cat_all} referees)\nsplit by gender")
        ax.set_xlabel("Birthyear")
        ax.set_ylabel("Number of referees\nby birthyear")
        ax.set_ylim(0, 40)
        ax.grid(axis='y')
        plt.savefig(f'stats_{category}.png', dpi=300, bbox_inches='tight')
        plt.close(ax.get_figure())


def main():
    graph_data()


if __name__ == '__main__':
    sys.exit(main())
