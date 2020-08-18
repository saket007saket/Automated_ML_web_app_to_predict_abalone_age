import pandas as pd
import numpy as np
from file_operations import file_methods
from data_preprocessing import preprocessing
from data_ingestion import data_loader_prediction
from application_logging import logger
from Prediction_Raw_Data_Validation.predictionDataValidation import Prediction_Data_validation


class prediction:

    def __init__(self,path):
        self.file_object = open("Prediction_Logs/Prediction_Log.txt", 'a+')
        self.log_writer = logger.App_Logger()
        self.pred_data_val = Prediction_Data_validation(path)

    def predictionFromModel(self):

        try:
            self.pred_data_val.deletePredictionFile() #deletes the existing prediction file from last run!
            self.log_writer.log(self.file_object,'Start of Prediction')
            data_getter=data_loader_prediction.Data_Getter_Pred(self.file_object,self.log_writer)
            data=data_getter.get_data()


            preprocessor = preprocessing.Preprocessor(self.file_object, self.log_writer)
            data = preprocessor.remove_columns(data,[])  # remove the column as it doesn't contribute to prediction.
            data.replace('?', np.NaN, inplace=True)  # replacing '?' with NaN values for imputation

            # check if missing values are present in the dataset
            is_null_present, cols_with_missing_values = preprocessor.is_null_present(data)

            # if missing values are there, replace them appropriately.
            if (is_null_present):
                data = preprocessor.impute_missing_values(data, cols_with_missing_values)  # missing value imputation
            # encode categorical data
            #data = preprocessor.encode_categorical_columns(data)
            df=data.copy()
            df.drop(labels=['Sex'],axis=1,inplace=True)

            file_loader = file_methods.File_Operation(self.file_object, self.log_writer)
            kmeans = file_loader.load_model('KMeans')

            ##Code changed

            clusters=kmeans.predict(df)
            data['clusters']=clusters
            data = preprocessor.encode_categorical_columns(data)
            clusters=data['clusters'].unique()
            predictions=[]
            for i in clusters:
                cluster_data = data[data['clusters'] == i]
                cluster_data = cluster_data.drop(['clusters'],axis=1)
                model_name = file_loader.find_correct_model_file(i)
                model = file_loader.load_model(model_name)
                result = (model.predict(np.array(cluster_data)))
                for res in result:
                    if res == 0:
                        predictions.append('1-8 Rings')
                    elif res == 1:
                        predictions.append('11+ Rings')
                    else:
                        predictions.append('9-10 Rings')

            final= pd.DataFrame(list(zip(predictions)),columns=['Predictions'])
            path="Prediction_Output_File/Predictions.csv"
            final.to_csv("Prediction_Output_File/Predictions.csv",header=True,mode='a+') #appends result to prediction file
            self.log_writer.log(self.file_object,'End of Prediction')
        except Exception as ex:
            self.log_writer.log(self.file_object, 'Error occured while running the prediction!! Error:: %s' % ex)
            raise ex
        return path , final



