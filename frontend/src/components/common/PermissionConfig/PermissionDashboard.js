import React, { useState } from "react";

import { makeStyles } from "@material-ui/core/styles";
import Paper from "@material-ui/core/Paper";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableContainer from "@material-ui/core/TableContainer";
import TableHead from "@material-ui/core/TableHead";
import TablePagination from "@material-ui/core/TablePagination";
import TableRow from "@material-ui/core/TableRow";

import "assets/style/PermissionDashboard.css";

const useStyles = makeStyles({
  root: {
    width: "100%",
  },
  container: {
    maxHeight: "85%",
  },
});

const PermissionDashboard = ({ tableHeaderData, tableBodyData }) => {
  const classes = useStyles();

  // Hooks for Pagination
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(+event.target.value);
    setPage(0);
  };

  return (
    <Paper className={classes.root}>
      <TableContainer className={classes.container}>
        <Table stickyHeader aria-label="sticky table">
          <TableHead>
            <TableRow>
              {tableHeaderData.map((header) => (
                <TableCell
                  key={header.id}
                  align={"center"}
                  // In the future, with more permission, activate this.
                  // style={{ width: 200 }}
                >
                  {header.label}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {tableBodyData
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((eachUser) => {
                return (
                  <TableRow
                    hover
                    role="checkbox"
                    tabIndex={-1}
                    key={eachUser["auth0-user-id"]}
                  >
                    {tableHeaderData.map((header) => {
                      const value = eachUser[header.id];
                      return (
                        <TableCell
                          key={header.id}
                          align={"center"}
                          style={
                            header.id === "auth0-user-id"
                              ? {
                                  backgroundColor: "white",
                                  /* In the future, with more permission, activate this to make first column to be fixed
                                    position: "sticky",
                                    left: 0,
                                    zIndex: 1,
                                  */
                                }
                              : value === "true"
                              ? {
                                  backgroundColor: "#7CAF80",
                                  borderLeft: "1px soild white",
                                  borderRight: "1px solid white",
                                }
                              : {
                                  backgroundColor: "#ff6666",
                                  borderLeft: "1px soild white",
                                  borderRight: "1px solid white",
                                }
                          }
                        >
                          {header.id === "auth0-user-id" ? value : null}
                        </TableCell>
                      );
                    })}
                  </TableRow>
                );
              })}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        rowsPerPageOptions={[10, 25]}
        component="div"
        count={tableBodyData.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onChangePage={handleChangePage}
        onChangeRowsPerPage={handleChangeRowsPerPage}
      />
    </Paper>
  );
};

export default PermissionDashboard;
