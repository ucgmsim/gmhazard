import React, { useState, useEffect, Fragment } from "react";

import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { makeStyles } from "@material-ui/core/styles";
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";
import ListItemText from "@material-ui/core/ListItemText";
import ListSubheader from "@material-ui/core/ListSubheader";
import Collapse from "@material-ui/core/Collapse";
import ExpandLess from "@material-ui/icons/ExpandLess";
import ExpandMore from "@material-ui/icons/ExpandMore";

import "assets/style/TwoColumnView.css";
import "katex/dist/katex.min.css";

// Reference
// https://webpack.js.org/guides/dependency-management/#requirecontext
const importAll = (r) => {
  return r.keys().map(r);
};
const getPrefixNum = (filePath) => {
  return filePath.substring(
    filePath.indexOf("a/") + 2,
    filePath.lastIndexOf("_")
  );
};
/* Read all the .md files in a given directory and sort them
  With three restrictions,
  1. The file must start with a number to sort properly
  2. Then followed by the subdirectory's title with an underscore
  3. Then the title of the document, if it needs a spacing between word, use a hyphen.
  Then it would look something like this.
  "/static/media/1_Hazard-test.bb7746c9.md"
*/
const markdownFiles = importAll(
  require.context("assets/documents", false, /\.md$/)
).sort((a, b) => {
  return getPrefixNum(a) - getPrefixNum(b);
});

// One of ways adding styles, this is specialized for Material-UI
const useStyles = makeStyles((theme) => ({
  root: {
    width: "100%",
    backgroundColor: theme.palette.background.paper,
  },
  nested: {
    paddingLeft: theme.spacing(4),
  },
}));

// Similar to getPrefixNum, instead we get something after number underscore
// Currently will be either Hazard or Projects
const getHeaderTitle = (filePath) => {
  return filePath.substring(filePath.indexOf("_") + 1, filePath.indexOf("-"));
};

const getFilename = (filePath) => {
  return filePath
    .substring(filePath.indexOf("-") + 1, filePath.lastIndexOf("."))
    .split(".")[0];
};

const FrameworkDocView = () => {
  const classes = useStyles();

  const [selectedDoc, setSelectedDoc] = useState({
    header: "",
    body: "",
  });

  const [markdownFilesObj, setMarkdownFilesObj] = useState({});

  // Unfortunately, we cannot create state hook dynamically, so must be hardcoded to control
  // each dropdown
  const [open, setOpen] = useState({
    Hazard: false,
    Projects: false,
  });

  // Used an object to the state, to change the certain property's value
  const handleClick = (status) => {
    setOpen((prevState) => ({
      ...prevState,
      [status]: !open[status],
    }));
  };

  /* This is the object that contains the information of the directory with files and its content.
    E.g. {
      Hazard : {
        site-selection: contents,
        seismic-hazard: contents,
        gms: contents,
      },
      projects : {
        site-selection: contents,
        seismic-hazard: contents,
        gms: contents,
      }
    }
    1_Hazard-Site-Selection.md
    Outer object's property is the subdirectory's title.
    Inner object's property is the title of the document which will be displayed
    in the list as a clickable item.
    and its value, contents, are the one to be displayed in the right column, the viewer.
  */
  useEffect(() => {
    let tempObj = {};

    const loadMarkdowns = async () => {
      for (let i = 0; i < markdownFiles.length; i++) {
        const file = markdownFiles[i];

        const subHeaderTitle = getHeaderTitle(file);

        const fileName = getFilename(file);

        if (tempObj.hasOwnProperty(subHeaderTitle) === false) {
          tempObj[subHeaderTitle] = {};
        }

        await fetch(file).then(async (response) => {
          const responseData = await response.text();
          tempObj[subHeaderTitle][fileName] = responseData;
        });
      }

      setMarkdownFilesObj(tempObj);
    };

    loadMarkdowns();
  }, []);

  return (
    <div className="two-column-inner">
      <div className="row two-column-row">
        <div className="col-3 controlGroup form-panel">
          <List
            component="nav"
            aria-labelledby="nested-list-subheader"
            subheader={
              <ListSubheader component="div" id="nested-list-subheader">
                Documents
              </ListSubheader>
            }
            className={classes.root}
          >
            {Object.keys(markdownFilesObj).map((title) => {
              return (
                <Fragment>
                  <ListItem button onClick={() => handleClick(title)}>
                    <ListItemText>{title}</ListItemText>
                    {open[title] ? <ExpandLess /> : <ExpandMore />}
                  </ListItem>
                  <Collapse in={open[title]} timeout="auto" unmountOnExit>
                    <List component="div" disablePadding>
                      {Object.keys(markdownFilesObj[title]).map((fileName) => (
                        <ListItem
                          button
                          className={classes.nested}
                          onClick={() =>
                            setSelectedDoc({
                              header: title,
                              body: fileName,
                            })
                          }
                        >
                          <ListItemText>
                            {fileName.includes("-")
                              ? fileName.replaceAll("-", " ")
                              : fileName}
                          </ListItemText>
                        </ListItem>
                      ))}
                    </List>
                  </Collapse>
                </Fragment>
              );
            })}
          </List>
        </div>
        <div className="col-9 controlGroup form-viewer">
          <div className="two-column-view-right-pane">
            {selectedDoc["header"] !== "" && selectedDoc["body"] !== "" ? (
              <ReactMarkdown
                children={
                  markdownFilesObj[selectedDoc["header"]][selectedDoc["body"]]
                }
                remarkPlugins={[remarkMath]}
                rehypePlugins={[rehypeKatex]}
              />
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FrameworkDocView;
