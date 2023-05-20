

<h1 align="center">OntMetaScript</h1>



<p align="center">
  <a href="#dart-about">About</a> &#xa0; | &#xa0; 
  <a href="#sparkles-features">Features</a> &#xa0; | &#xa0;
  <a href="#rocket-technologies">Technologies</a> &#xa0; | &#xa0;
  <a href="#white_check_mark-requirements">Requirements</a> &#xa0; | &#xa0;
  <a href="#checkered_flag-starting">Starting</a> &#xa0; | &#xa0;
  <a href="#memo-license">License</a> &#xa0; 
</p>

<br>

## :dart: About ##

 A little python script that was developed during my master thesis. It accumulates Ontology metadata from .owl or .ttl files making my work easier. This script is not fully vetted and is just a quick python script made on the fly. The data collected with this can be found under the following doi at zenodo.org 10.5281/zenodo.7895261

## :sparkles: Features ##

:heavy_check_mark: Extraction of ontology size(properties and classes)
:heavy_check_mark: Extraction of five random ontology classes for further analysis
:heavy_check_mark: OOPS Report generation
:heavy_check_mark: FOOPS Report generation
:heavy_check_mark: Faircheck Report generation

## :rocket: Technologies ##

The following tools were used in this project:

- [Python](https://www.python.org/)
- [Owlready2](https://github.com/pwin/owlready2)
- [alive-progress](https://github.com/rsalmei/alive-progress)
- [rdflib](https://github.com/RDFLib/rdflib)
- [OntOlogy Pitfall Scanner!](https://oops.linkeddata.es/)
- [Ontology Pitfall Scanner For FAIR](https://foops.linkeddata.es/FAIR_validator.html)
- [Fair-Checker](https://fair-checker.france-bioinformatique.fr/check)

## :white_check_mark: Requirements ##

Before starting :checkered_flag: you need to install the requirements in the requirements.txt. :checkered_flag: Furthermore, an internet connection is reuqired as the FOOPS, OOPS and Faircheck reports are queried through API calls.

## :checkered_flag: Starting ##

```bash
# Clone this project
$ git clone https://github.com/SupaaSchnitzel/ontmetascript

# Access
$ cd ontmetascript

# Install dependencies
$ pip install -r requirements.txt

# Print help
$ python OntMeta.py -h

# Basic Usage
$ python OntMeta.py -a [Folder with the Ontolgy Files]

# The script will put the results ./analysis/ by default
```

## :memo: License ##

This project is under license from MIT. For more details, see the [LICENSE](LICENSE.md) file.


&#xa0;

<a href="#top">Back to top</a>
