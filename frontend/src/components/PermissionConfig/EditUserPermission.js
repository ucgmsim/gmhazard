import React, { useState, useEffect } from "react";

import Select from "react-select";
import { v4 as uuidv4 } from "uuid";

import { useAuth0 } from "components/common/ReactAuth0SPA";
import * as CONSTANTS from "constants/Constants";

import { ModalComponent } from "components/common";
import {
  handleErrors,
  createProjectIDArray,
  APIQueryBuilder,
} from "utils/Utils";

const EditUserPermission = () => {
  const { getTokenSilently } = useAuth0();

  const [userData, setUserData] = useState({});
  const [addableProjectData, setAddableProjectData] = useState([]);
  const [allocatedProjectData, setAllocatedProjectData] = useState([]);

  const [userOption, setUserOption] = useState([]);
  const [addableProjectOption, setAddableProjectOption] = useState([]);
  const [allocatedProjectOption, setAllocatedProjectOption] = useState([]);

  const [selectedUser, setSelectedUser] = useState([]);
  const [selectedAddableProject, setSelectedAddableProject] = useState([]);
  const [selectedAllocatedProject, setSelectedAllocatedProject] = useState([]);

  const [userDataFetching, setUserDataFetching] = useState(false);
  const [projectDataFetching, setProjectDataFetching] = useState(false);

  const [alocateClick, setAllocateClick] = useState(null);
  const [addableStatusText, setAddableStatusText] =
    useState("Allocate Project");

  const [removeClick, setRemoveClick] = useState(null);
  const [allocatedStatusText, setAllocatedStatusText] =
    useState("Remove Project");

  const [addModal, setAddModal] = useState(false);
  const [removeModal, setRemoveModal] = useState(false);

  // Create react-select options(readable objects) for users
  useEffect(() => {
    if (Object.entries(userData).length > 0) {
      setUserOption(createProjectIDArray(userData));
    }
  }, [userData]);

  // Create react-select options(readable objects) for addable projects
  useEffect(() => {
    if (Object.entries(addableProjectData).length > 0) {
      setAddableProjectOption(createProjectIDArray(addableProjectData));
    } else {
      setAddableProjectOption([]);
    }
  }, [addableProjectData]);

  // Create react-select options(readable objects) for removable projects
  useEffect(() => {
    if (Object.entries(allocatedProjectData).length > 0) {
      setAllocatedProjectOption(createProjectIDArray(allocatedProjectData));
    } else {
      setAllocatedProjectOption([]);
    }
  }, [allocatedProjectData]);

  // Fetching user information from the Auth0
  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const getUserInfo = async () => {
      try {
        const token = await getTokenSilently();

        setUserDataFetching(true);

        await fetch(
          CONSTANTS.INTERMEDIATE_API_URL +
            CONSTANTS.INTERMEDIATE_API_AUTH0_USERS_ENDPOINT,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
            signal: signal,
          }
        )
          .then(handleErrors)
          .then(async (users) => {
            const responseUserData = await users.json();
            setUserData(responseUserData);
            setUserDataFetching(false);
          })
          .catch((error) => {
            console.log(error);
          });
      } catch (error) {
        console.log(error);
      }
    };

    getUserInfo();

    return () => {
      abortController.abort();
    };
  }, []);

  // Fetching projects that are not allocated to a user.
  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const getAddableProjectData = async () => {
      if (selectedUser.length !== 0) {
        // Reset the selected option
        setSelectedAddableProject([]);
        setSelectedAllocatedProject([]);

        setAddableProjectOption([]);
        setAllocatedProjectOption([]);

        setProjectDataFetching(true);

        try {
          const token = await getTokenSilently();

          await Promise.all([
            fetch(
              CONSTANTS.INTERMEDIATE_API_URL +
                CONSTANTS.INTERMEDIATE_API_ALL_PRIVATE_PROJECTS_ENDPOINT,
              {
                headers: {
                  Authorization: `Bearer ${token}`,
                },
                signal: signal,
              }
            ),
            fetch(
              CONSTANTS.INTERMEDIATE_API_URL +
                CONSTANTS.INTERMEDIATE_API_USER_PROJECTS_ENDPOINT +
                APIQueryBuilder({
                  user_id: selectedUser.value,
                }),
              {
                headers: {
                  Authorization: `Bearer ${token}`,
                },
                signal: signal,
              }
            ),
          ])

            .then(handleErrors)
            .then(async ([allPrivateProjects, userProjects]) => {
              const allPrivateProjectsData = await allPrivateProjects.json();
              const userProjectsData = await userProjects.json();

              // Compare Users_Projects table and Project table with Private access_level
              setAddableProjectData(
                filterToGetAddableProjects(
                  allPrivateProjectsData,
                  userProjectsData
                )
              );

              setAllocatedProjectData(
                filterToGetAllowedProjects(userProjectsData)
              );

              setProjectDataFetching(false);
            })
            .catch((error) => {
              console.log(error);
            });
        } catch (error) {
          console.log(error);
        }
      }
    };

    getAddableProjectData();

    return () => {
      abortController.abort();
    };
  }, [selectedUser]);

  // Allocating selected projectst to the chosen user
  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const allocateProjects = async () => {
      if (alocateClick !== null) {
        try {
          setAddableStatusText("Allocating...");
          const token = await getTokenSilently();

          let requestOptions = {
            method: "POST",
            headers: {
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({
              user_info: selectedUser,
              project_info: selectedAddableProject,
            }),
            signal: signal,
          };

          await fetch(
            CONSTANTS.INTERMEDIATE_API_URL +
              CONSTANTS.INTERMEDIATE_API_USER_ALLOCATE_PROJECTS_ENDPOINT,
            requestOptions
          )
            .then(handleErrors)
            .then(async () => {
              setAddableStatusText("Allocate Project");
            })
            .catch((error) => {
              console.log(error);
              setAddableStatusText("Error occurred");
            });
        } catch (error) {
          console.log(error);
          setAddableStatusText("Error occurred");
        }
      }
    };

    allocateProjects();

    return () => {
      abortController.abort();
    };
  }, [alocateClick]);

  // Removing projects from the chosen user
  useEffect(() => {
    const abortController = new AbortController();
    const signal = abortController.signal;

    const removeProjects = async () => {
      if (removeClick !== null) {
        try {
          setAllocatedStatusText("Removing...");
          const token = await getTokenSilently();

          let requestOptions = {
            method: "POST",
            headers: {
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({
              user_info: selectedUser,
              project_info: selectedAllocatedProject,
            }),
            signal: signal,
          };

          await fetch(
            CONSTANTS.INTERMEDIATE_API_URL +
              CONSTANTS.INTERMEDIATE_API_USER_REMOVE_PROJECTS_ENDPOINT,
            requestOptions
          )
            .then(handleErrors)
            .then(async () => {
              setAllocatedStatusText("Removing...");
            })
            .catch((error) => {
              console.log(error);
              setAllocatedStatusText("Error occurred");
            });
        } catch (error) {
          console.log(error);
          setAllocatedStatusText("Error occurred");
        }
      }
    };

    removeProjects();

    return () => {
      abortController.abort();
    };
  }, [removeClick]);

  // Reset the select field after the modal is closed.
  useEffect(() => {
    if (addModal === false && setAllocateClick !== null) {
      setSelectedAddableProject([]);
      setSelectedAllocatedProject([]);
      setAddableProjectOption([]);
      setAllocatedProjectOption([]);
      setSelectedUser([]);
    }
  }, [addModal]);

  useEffect(() => {
    if (removeModal === false && setRemoveClick !== null) {
      setSelectedAddableProject([]);
      setSelectedAllocatedProject([]);
      setAddableProjectOption([]);
      setAllocatedProjectOption([]);
      setSelectedUser([]);
    }
  }, [removeModal]);

  const allocateProjects = () => {
    setAllocateClick(uuidv4());
    setAddModal(true);
  };

  const removeProjects = () => {
    setRemoveClick(uuidv4());
    setRemoveModal(true);
  };

  const invalidBtn = (selectedProjects) => {
    return !(
      Object.entries(selectedUser).length > 0 && selectedProjects.length > 0
    );
  };

  const modalBodyText = (action, selectedProjects) => {
    let bodyString = `Successfully ${action} the following projects:\n\n`;

    for (let i = 0; i < selectedProjects.length; i++) {
      bodyString += `${i + 1}: ${selectedProjects[i].label}\n`;
    }

    bodyString += `\nto ${selectedUser.label}`;

    return bodyString;
  };

  const filterToGetAddableProjects = (allPrivateProjects, userProjects) => {
    let filteredProjects = {};

    for (const [key, value] of Object.entries(allPrivateProjects)) {
      if (!Object.keys(userProjects).includes(key)) {
        filteredProjects[key] = value;
      }
    }

    return filteredProjects;
  };

  const filterToGetAllowedProjects = (userProjects) => {
    let filteredProjects = {};

    for (const [key, value] of Object.entries(userProjects)) {
      filteredProjects[key] = value;
    }

    return filteredProjects;
  };

  return (
    <div className="container">
      <div className="row justify-content-lg-center">
        <div className="col-lg-6 mb-5">
          <h4>Choose a user</h4>
          <Select
            id="available-users"
            onChange={(value) => setSelectedUser(value || [])}
            value={selectedUser}
            options={userOption}
            isDisabled={userDataFetching === true}
            placeholder={
              userDataFetching === true
                ? `${CONSTANTS.PLACEHOLDER_LOADING}`
                : `${CONSTANTS.PLACEHOLDER_SELECT_SIGN}`
            }
            menuPlacement="auto"
            menuPortalTarget={document.body}
          />
        </div>
      </div>
      <div className="row justify-content-lg-center">
        <div className="col-lg-6">
          <h4>Allowed Private Projects</h4>
          <h5>(Use to remove projects from a user)</h5>
          <Select
            id="allowed-projects"
            onChange={(value) => setSelectedAllocatedProject(value || [])}
            value={selectedAllocatedProject}
            options={allocatedProjectOption}
            isMulti
            closeMenuOnSelect={false}
            isDisabled={allocatedProjectOption.length === 0}
            menuPlacement="auto"
            placeholder={
              selectedUser.length === 0
                ? "Please select a user first..."
                : selectedUser.length !== 0 &&
                  projectDataFetching === true &&
                  allocatedProjectOption.length === 0
                ? `${CONSTANTS.PLACEHOLDER_LOADING}`
                : selectedUser.length !== 0 &&
                  projectDataFetching === false &&
                  allocatedProjectOption.length === 0
                ? "No allowed projects"
                : selectedUser.length !== 0 &&
                  allocatedProjectOption.length !== 0
                ? "Select projects to remove"
                : "Something went wrong"
            }
          />
          <button
            id="remove-selected-projects-btn"
            type="button"
            className="btn btn-primary mt-4"
            onClick={() => removeProjects()}
            disabled={invalidBtn(selectedAllocatedProject)}
          >
            {allocatedStatusText}
          </button>
        </div>

        <div className="col-lg-6">
          <h4>Addable Private Projects</h4>
          <h5>(Use to add projects to a user)</h5>
          <Select
            id="available-projects"
            onChange={(value) => setSelectedAddableProject(value || [])}
            value={selectedAddableProject}
            options={addableProjectOption}
            isMulti
            closeMenuOnSelect={false}
            isDisabled={addableProjectOption.length === 0}
            menuPlacement="auto"
            placeholder={
              selectedUser.length === 0
                ? "Please select a user first..."
                : selectedUser.length !== 0 &&
                  projectDataFetching === true &&
                  addableProjectOption.length === 0
                ? `${CONSTANTS.PLACEHOLDER_LOADING}`
                : selectedUser.length !== 0 &&
                  projectDataFetching === false &&
                  addableProjectOption.length === 0
                ? "No addable projects"
                : selectedUser.length !== 0 && addableProjectOption.length !== 0
                ? "Select projects to allocate"
                : "Something went wrong"
            }
          />
          <button
            id="allocate-user-submit-btn"
            type="button"
            className="btn btn-primary mt-4"
            onClick={() => allocateProjects()}
            disabled={invalidBtn(selectedAddableProject)}
          >
            {addableStatusText}
          </button>
        </div>
      </div>

      <ModalComponent
        modal={addModal}
        setModal={setAddModal}
        title="Successfully added"
        body={modalBodyText("added", selectedAddableProject)}
      />

      <ModalComponent
        modal={removeModal}
        setModal={setRemoveModal}
        title="Successfully removed"
        body={modalBodyText("removed", selectedAllocatedProject)}
      />
    </div>
  );
};

export default EditUserPermission;
