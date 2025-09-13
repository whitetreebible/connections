# Bible Atlas

Welcome to **Bible Atlas**, an interactive resource for exploring biblical people, places, tribes, and themes. This project visualizes relationships across the Bible and related sources, providing a rich reference for pastors, scholars, and curious readers alike.

Bible Atlas was created by a software engineer with a passion for biblical studies. It applies **network and graph theory** to connect ideas, themes, people, and places, offering both intuitive exploration and scholarly depth.

---

## What Bible Atlas Does

- Maps biblical relationships: who is connected to whom, familial lineages, tribal affiliations, and thematic links.  
- Each **page** includes references, notes, and visualizations showing its **connections** to other pages.  
- Includes **Old Testament, New Testament, and extra-biblical references** for every page.  
- Highlights **strong and weak connections** to help identify important links and scholarly debates.  
- Supports **modular expansion**: new pages, connections, or categories can be added via structured data (YAML) files.

---

## How to Use

### Browsing
- Search for primary agents like **People**, **Places**, **Tribes**, and **Themes** using the search bar or nav panel.
- Click on a page to view detailed information, references, notes, and visualizations of its connections.

### References
- Biblical references link to authoritative sources (BibleHub).
- Academic and extra-biblical references are listed for further study.

### Visualizations
- Each page may include charts showing connections (family, tribal, thematic).  
- Charts are generated from the underlying data, so new pages automatically appear.

---

## Contributing

### Financial Contributors

Someday, I would love to spend more than a few hours here or there on nights and weekends contributing to this project, but my day-job is still a big part of my life. Once I setup a way to donate, I'll have a way to track if this is a project that can be supported by my full-time work. I'll keep you posted.

### Academic Contributors
As a Bible enthusiast, I hope that others who love to study the Bible want to contribute to this (rather large) potential body of work! I welcome emails and 

### Software Dev Contributors

We welcome contributions! To add new pages or update connections:  

1. Create or modify YAML files in the `data/` folder.  
2. Run the **build script** to generate updated Markdown pages.  
3. Submit a pull request to the repository for review.

For more details, see out [contribution guidelines](devs/contributing.md)

### Email Updates
<script src="https://js-na2.hsforms.net/forms/embed/243805031.js" defer></script>
<div class="hs-form-frame" data-region="na2" data-form-id="1dae0866-beca-4bf7-a76d-83825456fa3b" data-portal-id="243805031"></div>

---

## Priority List
### Phase 1: POC
- complete 2025-09-04 (ish)
- it demonstrated the graphs in a manual way that seemed promising!
### Phase 2: Core Build
- refactor/rename/rebuild so it's scalable/testable/usable - done!
- in progress!
- blockers to get to Phase 3
  - must haves:
    - ... I think they're done now? testing/classes
  - nice to haves:
    - identify a good way to add incrementally instead of rebuilding everything. versions on nodes?
    - transition away from makefile, I need a better script runner framework
    - create a way to heal/suggest missing reciprocal links
### Phase 3: Import Genesis
- all of Genesis links--mostly by hand according to defined categories
- this does not include any academic resources, just Bible
### Phase 4: Torah
- add subscription/payment ability
- share with trusted academics/pastors/influencers
- complete Ex-De
### Phase 5
- See where it goes?

---

## Project Structure

> [TODO]()
> Need to fill out the project structure a bit...
