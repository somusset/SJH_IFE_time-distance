# To-do list before launching beta-test

- Review and modify classification export:
    - Adapt classification structure to be able to use existing reducer for line object
    - ~~Add question field to take into account the options when not submitting any line~~

- Ask Zooniverse team if we should or should not take classifications from users who are not logged in (guest users)
    - If the answer is that we should not, implement a way to require log in before classifying

- ~~Figure out how to load the movies and link them to the subjects~~
- ~~Adapt the code to display the movies as intended~~

- Think about axis for the time-distance plot: needed? confusing? what is possible within streamlit and canvas? --> probably unnecessary, I removed the arrow

- Little bugs to fix:
    - ~~Change color map to the original AIA map?~~
    - ~~Make sure the radio options reset to nothing once a new subject is loaded~~
    - Implement the "submit and talk" option the same way it works on usual Zooniverse FE --> need help with this
    - Color the submit buttons like it is on Zooniverse --> probably not easy, TBD if worth it

# To-do list before official launching

1. Run the beta-test and implement feedback 
2. Prepare full subject set(s) 
