import pandas as pd
import numpy as np
import joblib
import collections

df = pd.read_pickle('data/research_data_28002.pkl')
cat = joblib.load('models/Catboost_apart_28002.pkl')
lgb = joblib.load('models/LGB_apart_28002.pkl')
d_ = joblib.load('models/def_dict_28002.pkl')
data_m = joblib.load('data/merge_data_28002.pkl')

d_r_m_f_s = ['district','rooms','max_floors','floor','street']

def gb_fe(df,cols,targ,typ='mean'):
    for col in range(len(cols)):
        df['_'.join(cols[col:])+'_'+typ] = df.groupby(cols[col:])[targ].transform(typ).fillna(0)

def prep(dfs):
    tmp=data_m.append(dfs)
    for i in tmp.iloc[:,:7]:
        if tmp[i].isna().sum()>0:
            tmp[i]=tmp[i].fillna(tmp.groupby('street')[i].transform(lambda x: x.mode()[0]))
    for i in ['mean','std','min','max']:
        gb_fe(tmp,d_r_m_f_s,'rubm2',i)
    tmp['count_by_dist'] = tmp.groupby(['district','street']).dom.transform('count')
    tmp['count_by_str'] = tmp.groupby(['street']).dom.transform('count')
    tmp.drop('rubm2',axis=1,inplace=True)
    tmp= tmp.iloc[-dfs.shape[0]:]
    for i in d_.keys():
        tmp[i] = d_[i].transform(tmp[i])
    return tmp



def data_input(data=None):
    d = collections.defaultdict(list)
    for info in cat.feature_names_[:7]:
        print( f'Input {info}, example :{df[info].unique()[:3]}')
        d[info] = input()
    d['dom'] = int(d['dom'])
    d['floor'] = int(d['floor'])
    d['max_floors']=int(d['max_floors'])
    d['m2']=float(d['m2'].replace(',','.'))
    d['rooms'] = str(d['rooms'])
    d['street'] = df[df.street.str.lower().str.contains(d['street'].lower())].street.mode()[0]
    home_df = pd.DataFrame(d,index=[0]).replace('',np.NaN)
    return home_df


            
                  
def predict(data,alg=lgb):
    print('Choose algoritm by his num:')
    for i,al in enumerate([cat,lgb]):
        print(i,' ',al.__class__.__name__)
    num = input()
    if num=='':
        price = [model.predict(data)[0] for model in [cat,lgb]]
    else :
        alg = [cat,lgb][int(num)]
        price=alg.predict(data)
    return(price)                  

new_data = data_input() 
fix_data = prep(new_data)                  
pr = predict(fix_data)
print(pr,'\n Mean: ',np.mean(pr))
