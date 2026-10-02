
import {
  Avatar,
  ListItemAvatar,
} from '@mui/material';

import FolderIcon from '@mui/icons-material/Folder';
import ImageIcon from '@mui/icons-material/Image';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';
import MusicNoteIcon from '@mui/icons-material/MusicNote';
import QueueMusicIcon from '@mui/icons-material/QueueMusic';

const FolderTypeAvatar = ({ type }) => (
  <ListItemAvatar>
    <Avatar>
      {type === 'directory' && <FolderIcon />}
      {type === 'file' && <MusicNoteIcon />}
      {type === 'image' && <ImageIcon />}
      {type === 'playlist' && <QueueMusicIcon />}
      {type === 'other' && <InsertDriveFileIcon />}
    </Avatar>
  </ListItemAvatar>
);

export default FolderTypeAvatar;
