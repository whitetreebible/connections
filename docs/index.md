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

We welcome contributions! To add new pages or update connections:  

1. Create or modify YAML files in the `data/` folder.  
2. Run the **build script** to generate updated Markdown pages.  
3. Submit a pull request to the repository for review.

For more details, see out [contribution guidelines](devs/contributing) and [schema](devs/schema).

---

## Project Structure

