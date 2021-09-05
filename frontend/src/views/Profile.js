import React from "react";
import { Container } from "reactstrap";

import { Loading } from "components/common";
import { useAuth0 } from "../components/common/ReactAuth0SPA";

const Profile = () => {
  const { loading, user } = useAuth0();

  if (loading || !user) {
    return <Loading />;
  }

  return <Container className="mb-5">Something to be here</Container>;
};

export default Profile;
