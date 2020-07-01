import pandas as pd
import joblib
import collections

df = pd.read_pickle('data/research_data.pkl')
gb_distr_rubm2=pd.read_csv('data/gb_district_rubm2.csv')
gb_distr_count=pd.read_csv('data/gb_district.csv')
gb_street_count=pd.read_csv('data/gb_street_count.csv')
knn = joblib.load('models/KNN_apart.pkl')
cat = joblib.load('models/Catboost_apart.pkl')
lgb = joblib.load('models/LGB_apart.pkl')
d_ = joblib.load('models/def_dict.pkl')
def predict_price(data=None,log1p=False,alg=lgb):
    if data!= None:
        d=data
        d['m2_range']=df['m2_range'].unique()[[(d['m2'] in i ) for i in df['m2_range'].unique()]][0]
    else:
        d = collections.defaultdict(list)
        for info in cat.feature_names_[:-4]:
            print( f'Input {info}, example :{df[info].unique()[:3]}')
            d[info] = input()
        d['dom'] = int(d['dom'])
        d['floor'] = int(d['floor'])
        d['max_floors']=int(d['max_floors'])
        d['m2']=float(d['m2'].replace(',','.'))
        d['m2_range']=df['m2_range'].unique()[[(d['m2'] in i ) for i in df['m2_range'].unique()]][0]
        d['rooms'] = str(d['rooms'])
    d['street'] = df[df.street.str.contains(d['street'])].street.mode()[0]
    home_df = pd.DataFrame(d,index=[0])
    for i in [gb_distr_rubm2,gb_distr_count,gb_street_count]:
        home_df = home_df.merge(i, how='left',on=i.columns[:-1].to_list())
    try:
        cat_df=home_df.apply(lambda x: d_[x.name].transform(x) if x.name in list(d_.keys()) else x)
    except:
        try:
            street = df[df.street.str.contains(d['street'])].street.mode()[0]
            idx_nearest=df.query('street==@street')['dom'].apply(lambda x: abs(x-d['dom'])).sort_values()[:1].index[0]
            home_df.loc[0,'dom'] = df['dom'].loc[idx_nearest]
            home_df['clean'] = home_df['street'] + ','+home_df['dom'].astype(str)
            print('some info from : ',home_df['clean'][0])
            cat_df=home_df.apply(lambda x: d_[x.name].transform(x) if x.name in list(d_.keys()) else x)
        except:
            gb__=df.groupby(['district','rooms','max_floors'])['clean'].apply(pd.Series.mode).reset_index().drop('level_3',axis=1)
            home_df=home_df.merge(gb__,how='left',on=gb__.columns.to_list()[:-1])
            home_df[['street','dom']] = home_df.clean.str.split(',',expand=True)
            print('some info from : ',home_df['clean'][0])
            cat_df=home_df.apply(lambda x: d_[x.name].transform(x) if x.name in list(d_.keys()) else x)
    cat_df = cat_df[cat.feature_names_]
    print('Choose algoritm with his num:')
    for i,al in enumerate([knn,cat,lgb]):
        print(i,' ',al.__class__.__name__)

    num = int(input())
    if num=='':
        num=2
    alg = [knn,cat,lgb][num]
    price=alg.predict(cat_df)
    return(price) 

pr = predict_price()
print(pr[0])