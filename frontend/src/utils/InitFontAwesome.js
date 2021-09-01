import { library } from "@fortawesome/fontawesome-svg-core";
import {
  faLink,
  faPowerOff,
  faUser,
  faDownload,
  faSpinner,
  faTrash,
  faCaretDown,
  faCaretUp,
  faFolderPlus,
  faBackspace,
  faQuestionCircle,
  faFileWord,
  faTools,
} from "@fortawesome/free-solid-svg-icons";

const InitFontAwesome = () => {
  library.add(faLink);
  library.add(faUser);
  library.add(faPowerOff);
  library.add(faDownload);
  library.add(faSpinner);
  library.add(faTrash);
  library.add(faCaretDown);
  library.add(faCaretUp);
  library.add(faFolderPlus);
  library.add(faBackspace);
  library.add(faQuestionCircle);
  library.add(faFileWord);
  library.add(faTools);
};

export default InitFontAwesome;
