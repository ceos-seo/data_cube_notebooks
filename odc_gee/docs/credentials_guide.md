# Getting service account credentials
This document is to help guide users through obtaining a service account
credentials file for use with GEE.

The first step is to setup the API to use the
[Google Earth Engine REST
API](https://developers.google.com/earth-engine/reference). To do
this you need to create a project [here](https://console.cloud.google.com/). Go
to the [API & Services
Dashboard](https://console.cloud.google.com/apis/dashboard)
from the developer console.

![](/docs/images/image1.png)

Select the button in the red box according to Figure 1. This will pull up the
API library. Search for Earth Engine, select it, and then enable it for the
project.

The next step to setup the API is to create a Service Account. To do this
navigate to the
[API
& Services
Credentials](https://console.cloud.google.com/apis/api/earthengine.googleapis.com/credentials)
page for the API.

![](/docs/images/image2.png)

Click the button in the red box for Figure 2 and select Service Account. Fill
out the form
and click next. You will likely need to add Owner roles in the next section.
Click the Role selection box, type Owner in the filter field, and then select
the Owner choice to add it as the Role. Click next. In this section click add
key and select the JSON option. This will download a JSON file with your key’s
credentials for the Service Account. **Keep this file secure and don’t
lose it.** This file will act as the API key for accessing GEE data. Once
you’ve got the file, click done.

>**Note:** It may take some time for your credentials to propagate before they
can be used.

If you encounter any issues with using your service account credentials then
you may have to get the proper permission to use GEE with your account from
Google. This process will involve contacting Google where you may have to
supply a Google employee your Service Account email as
indicated by the red box from the
[API
& Services
Credentials](https://console.cloud.google.com/apis/api/earthengine.googleapis.com/credentials)
page in Figure 3.

![](/docs/images/image3.png)
