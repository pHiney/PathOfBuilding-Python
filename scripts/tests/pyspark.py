import json
import pandas as pd

j = '''{
   "result":{
      "version":"1.2",
      "timeStamp":"2023-08-14 14:00:12",
      "description":"",
      "data":{
         "DateTime_Received":"2023-08-14T14:01:10.4516457+01:00",
         "DateTime_Actual":"2023-08-14T14:00:12",
         "OtherInfo":null,
         "main":[
            {
               "Status":0,
               "ID":111,
               "details":null
            }
         ]
      },
      "tn":"aaa"
   }
}'''


text_json = json.loads(j)
result=text_json.get("result", "")
print(result.get("version", ""))

results = [result["version"], result["timeStamp"], result["description"], result["data"], result["tn"] ]
df = pd.DataFrame(results).transpose()
print(df)
