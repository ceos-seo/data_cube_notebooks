# Uruguay Random Forest

The following notebooks provide an example of using earth observation data from Open Data Cube to create and use a random forest classifier. Each notebook performs specific tasks that illustrate the methodology involved.   

### Notebooks: 
1. [Data Exploration](#1:-Data-Exploration) 
2. [Feature Egnineering](#2:-Feature-Engineering) 
3. [Model Building and Evaluation](#3:-Model-Building-and-Evaluation) 
4. [Display and Package Classifier](#4:-Display-and-Package-Classifier) 


## Notebook 1: Data Exploration

This notebook gives an introduction to the labels being used, and it explores the respective strengths and weaknesses of our dataset. We come to the conclusion that there is not enough data to train our model without needing to combine correlated classes/labels into larger categories. This combination of labels results in a better classifier as it allows us to provide more samples per label for training.

## Notebook 2: Feature Engineering

This notebook shows how the features corresponding to each label used by the classifier will be generated and exported. To do this we use Landsat 8 data pulled from the Open Datacube. The original values are then used in various calculations to get more meaningful data representations. We also explore the features themselves to understand the statistical characteristics each feature may hold. This can provide further insight later when we evaluate our model in the next notebook.

## Notebook 3: Model Building and Evaluation

This notebook displays the actual training and evaluation of the classifier. We import the data engineered in the previous notebook, and use that in training and testing. 

Hyper-parameter optimization is briefly explored in this notebook and provides significant improvement to the model. The search algorithm chosen was a Randomized CV search; considered primarily for its speed.  

After the training is done, our next goal is in evaluating the model. A few scoring metrics are used which can determine mean accuracy of the model for all labels, or we can get a score for each individual label. This can let us know if the model is being over fit or if particular labels should be scrutinized due to high inaccuracies.

## Notebook 4: Display and Package Classifier

We go through similar processes found in the previous notebooks such as importing Datacube data and creating the features that will be used for label determination. Once the data is formatted properly it is passed into the classifier and labels are then appended to it. We then display the results of our classifier through various images and by overlaying them on a map for easy corroboration of accuracy. In this process we see that forests are classified with good accuracy. So as an example we show that this entire process can be rewritten as a Python module for explicitly classifying areas as forest or not forest. This module can be found here: `./classifiers/forest_classifier.py`
