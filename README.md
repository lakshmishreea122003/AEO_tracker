# AEO_tracker

### Note: Celery will be include in this flow
![Logo](https://github.com/lakshmishreea122003/AEO_tracker/blob/main/Screenshot%202025-11-21%20212648.png)


All the features mentioned in the image above is implemented in the backed. 

### Task yet to be completed
- celery should be included. But redis which is required for celery is not getting installed on my windows. I will take permission to install it on my college's system and complete the project.
- I tried with both gpt and claude models. These models mention the citation data in some of its responses, but not in all. I will fix this aspect.
- The formula I used currenlty gives very low AEO scores as some componets used for calculating score like the url citation, competitor related data etc are null/0. This causes the AEO scores to be calculated incorrectly. I will revamp the approach I used to fetch the value of the final metrics used to calculate AEO scores.
- currently this is the sample output: https://drive.google.com/drive/folders/1XwB2LdzLBnY6ieJQH1oyT8HIi355mGYv
- I will include the project in seo dashboard repo after completion.
