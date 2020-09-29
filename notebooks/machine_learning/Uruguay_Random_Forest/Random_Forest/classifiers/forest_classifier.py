"""
An example module for classifying a forest.                                                                                                                                                                        
Copyright 2019 United States Government as represented by the Administrator
of the National Aeronautics and Space Administration. All Rights Reserved.

Portion of this code is Copyright Geoscience Australia, Licensed under the
Apache License, Version 2.0 (the "License"); you may not use this file
except in compliance with the License. You may obtain a copy of the License
at

   http://www.apache.org/licenses/LICENSE-2.0

The CEOS 2 platform is licensed under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0.

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations
under the License.
"""
import os
from sys import path
path.append("../../")

import datetime 
import numpy as np
import pandas as pd
import xarray as xr

from sklearn.externals import joblib
from utils.data_cube_utilities.dc_frac import frac_coverage_classify
from utils.data_cube_utilities.dc_mosaic import create_median_mosaic

def NDVI(dataset: xr.Dataset) -> xr.DataArray:
    return (dataset.nir - dataset.red)/(dataset.nir + dataset.red).rename("NDVI")

def NBR(dataset: xr.Dataset) -> xr.DataArray:
    return ((dataset.nir - dataset.swir2) / (dataset.swir2 + dataset.nir)).rename("NBR")

def NDWI_2(dataset: xr.Dataset) -> xr.DataArray:
    return (dataset.green - dataset.nir)/(dataset.green + dataset.nir).rename("NDWI_2")

def SCI(dataset: xr.Dataset) -> xr.DataArray:
    return ((dataset.swir1 - dataset.nir)/(dataset.swir1 + dataset.nir)).rename("SCI")

def PNDVI(dataset: xr.Dataset) -> xr.DataArray:

    nir = dataset.nir
    green = dataset.green
    blue = dataset.blue
    red = dataset.red

    return ((nir - (green + red + blue))/(nir + (green + red + blue))).rename("PNDVI")

def CVI(dataset: xr.Dataset) -> xr.DataArray:
    return (dataset.nir * (dataset.red / (dataset.green * dataset.green))).rename("CVI")

def CCCI(dataset: xr.Dataset) -> xr.DataArray:
    return ((dataset.nir - dataset.red)/(dataset.nir + dataset.red)).rename("CCCI")

def NBR2(dataset: xr.Dataset) -> xr.DataArray:
    return (dataset.swir1 - dataset.swir2)/(dataset.swir1 + dataset.swir2)


def coefficient_of_variance(da:xr.DataArray):
    return da.std(dim = "time")/da.mean(dim = "time")   

def NDVI_coeff_var(ds, mask = None):
    ds_ndvi = NDVI(ds)    
    masked_ndvi = ds_ndvi.where(mask)
    return coefficient_of_variance(masked_ndvi)  

def fractional_cover_2d(dataset: xr.Dataset) -> xr.DataArray:
    return  frac_coverage_classify(dataset, clean_mask= np.ones(dataset.red.values.shape).astype(bool))

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class DatasetError(Error):
    """Exception raised for errors in the Dataset.

    Attributes:
        message: explanation of the error
    """

    def __init__(self, message):
        self.message = message
        
class MaskError(Error):
    """Exception raised for errors in the mask.

    Attributes:
        message: explanation of the error
    """
    def __init__(self, message):
        self.message = message

class ForestClassifier:
    """A classifier object used in classifying given feature sets as forest or not forest.
    
    Attributes:
        model_path (string): The path to the binary Random Forest Classifier model file.
    """
    
    def __init__(self, model_path=None):
        """Inits ForestClassification with model location."""
        if(model_path is None):
            raise TypeError('model_path is NoneType. Please supply a string for model_path.')
            
        self.model_path = model_path
         
    def validate_xarray(self, dims, dataset: xr.Dataset):
        """Validates an Xarray Dataset
        
        Args:
            dims (tuple): An ordered list of the dimensions to check for in the Xarray Dataset.
            dataset (xarray.Dataset): The Xarray Dataset to validate.
            
        Returns:
            The dataset if it is valid and raises an exception otherwise.
        """
        error = '\nMissing Variables Exception:\n\tThe following Xarray variables are expected and in this order: {}\n\tThe following were present: {}\n\tThe following were missing: {}\n\tThe following appeared out of order: {}'
        missing = []
        order = []
        present = []
        for i in range(len(dims)):
            # Check if dimension is in dataset
            if(not hasattr(dataset, dims[i])):
                missing.append(dims[i])
            else:
                # Check if the order is the same as supplied tuple
                if(dataset.isel(time=0, latitude=0, longitude=0).to_array()[i].coords['variable'].data != dims[i]):
                    order.append(dims[i])
                present.append(dims[i])
        # Check if any of the previous validations failed
        if(len(missing) == 0 or len(order) == 0):
            return dataset
        else:
            raise DatasetError(error.format(dims, present, missing, order))
            
    def validate_mask(self, mask):
        """Validates the mask as boolean or boolean-like array.
        
        Args:
            mask: The mask to validate.
            
        Returns:
            A boolean mask if it is valid, otherwise an exception is raised.
        """
        if(mask is None):
            raise MaskError('\nMissing Variable Exception:\n\tPlease supply a boolean or boolean-like mask for cloud-free compositing.')
        elif(mask.values.dtype == bool):
            return mask
        # Check if mask is boolean-like (0 or 1) and convert to actual boolean
        elif(set(np.unique(mask.astype(int))).issubset(set([0, 1]))):
            return np.isin(mask.astype(int), [1])
        else:
            raise MaskError('\nVariable Type Exception:\n\tThe supplied mask is not boolean or boolean-like (ex: True/False or 1/0).')
        
    def build_features(self, dataset: xr.Dataset, mask=None) -> xr.Dataset:
        """Builds the features used by the classifier.
        
        Args:
            features (xarray.Dataset): An Xarray Dataset containing landsat8 values in the order of red, green, blue, nir, swir1, and swir2.
            mask (xarray.DataArray): A clean mask for creating the cloud free composite. If not used, pixel_qa is used to create one.
        
        Returns:
            The Xarray Dataset with the built features appended.  
        """
        # Validate the Dataset and check order of features
        REQUIRED_FEATURES = ('red',
                             'green',
                             'blue',
                             'nir',
                             'swir1',
                             'swir2'
                            )
        # Validate the dataset and mask
        dataset = self.validate_xarray(REQUIRED_FEATURES, dataset)
        mask = self.validate_mask(mask)
        
        
        composite = create_median_mosaic(dataset, clean_mask=mask)

        if(hasattr(composite, 'pixel_qa')):
            composite = composite.drop('pixel_qa')
            
        features = xr.Dataset()
        features = features.merge(composite)
        
        # Build an ordered tuple of the necessary features for classification
        feature_list = (NDVI,
                        NDVI_coeff_var,
                        PNDVI,
                        NBR,
                        NBR2,
                        NDWI_2,
                        SCI,
                        CVI,
                        CCCI,
                        fractional_cover_2d
                       )
        
        # Build the features by iterating over tuple of feature methods
        for i in range(len(feature_list)):
            if(feature_list[i].__name__ == 'NDVI_coeff_var'):
                features[feature_list[i].__name__] = feature_list[i](dataset, mask = mask)
            elif(feature_list[i].__name__ == 'fractional_cover_2d'):
                features = features.merge(fractional_cover_2d(composite))
            else:
                features[feature_list[i].__name__] = feature_list[i](composite)
        features.NDVI_coeff_var.values[ np.isnan(features.NDVI_coeff_var.values)] = 0
        
        return features
        
        
    def classify(self, dataset: xr.Dataset, mask=None) -> xr.Dataset:
        """Classifies the given dataset as forest or not forest.
        
        Args:
            dataset (xarray.Dataset): An Xarray Dataset containing landsat8 values in the order of red, green, blue, nir, swir1, and swir2 (will also need pixel_qa if no mask is supplied).
            mask (xarray.DataArray): A clean mask for creating the cloud free composite. If not used, pixel_qa is used to create one.
            
        Returns:
            An Xarray Dataset with forest label containing True/False for whether the given features are classified as a forest.
            
            True: Forest
            False: Not Forest
        """
        features = self.build_features(dataset, mask)
        
        # Convert the Dataset to a DataFrame for ease of use
        features = features.to_dataframe()
        
        # Load the model
        rf = joblib.load(self.model_path)
        
        # Grab the feature values as a numpy array and split into smaller chunks
        X = features.values
        X = np.array_split(X, 100)
        
        # Generate a classification for each chunk and concatenate into one array
        y_pred = []
        for i in range(len(X)):
            y_pred.append(rf.predict(X[i]))
        y_pred = np.concatenate(y_pred)
        y_pred = np.isin(y_pred, 'Forest')
        
        # Append the array to the features DataFrame
        df = pd.DataFrame(y_pred, columns=['forest'])
        features['forest'] = df.values
        
        # Return the DataFrame as a Dataset
        return xr.Dataset.from_dataframe(features)