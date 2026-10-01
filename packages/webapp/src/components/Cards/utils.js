import {
  isEmpty,
  has,
} from 'ramda';

import commands from '../../commands';
import { ACTIONS_MAP } from '../../config';

const mapValuesToKeys = (command, args) => {
  const argKeys = getCommandArgKeys(command);
  const values = argKeys.reduce((prev, arg, pos) => (
    {
      ...prev,
      [arg]: args[pos],
    }
    ), {});

  return values;
};

const getActionAndCommand = (actionData) => {
  const { action, command: { name } = {} } = actionData;

  return { action, command: name };
}

const findActionByCommand = (command) => {
  const action = Object.keys(ACTIONS_MAP).find((action) => {
    return has(command)(ACTIONS_MAP[action].commands)
  });

  return action;
};

const getCommandArgKeys = (command) => {
  const { [command] : { argKeys = [] } = {} } = commands;

  return argKeys;
};

const buildActionData = (action, command = {}, args = {}) => {
  const data = {
    action,
    command,
  };

  if (!isEmpty(command)) {
    const _args = Array.isArray(args)
      ? mapValuesToKeys(command, args)
      : args;

    data.command = {
      name: command,
      args: _args,
    }
  }

  return data;
};

// Commands sharing an action (e.g. the timers) are told apart by their fixed `cardArgs`.
const findCommandByCardAction = (cardAction, args = {}) => (
  Object.keys(commands).find(command => (
    commands[command].cardAction === cardAction
    && Object.entries(commands[command].cardArgs || {}).every(([key, value]) => args[key] === value)
  ))
);

// The card entry to register for the selected command: `{ action, args }` with named args.
const buildCardEntry = (actionData) => {
  const { command } = getActionAndCommand(actionData);
  const argKeys = getCommandArgKeys(command);
  const values = getArgsValues(actionData);
  const args = argKeys.reduce((prev, key, pos) => (
    values[pos] === undefined ? prev : { ...prev, [key]: values[pos] }
  ), { ...commands[command]?.cardArgs });

  return { action: commands[command]?.cardAction, args };
};

const getArgsValues = (actionData) => {
  const { command } = getActionAndCommand(actionData);
  const argKeys = getCommandArgKeys(command);
  const { [command]: { argDefaults = {} } = {} } = commands;

  return argKeys.map(
    key => (
      actionData.command.args[key] === undefined
        ? argDefaults[key]
        : actionData.command.args[key]
    )
  );
};

export {
  buildActionData,
  buildCardEntry,
  findActionByCommand,
  findCommandByCardAction,
  getActionAndCommand,
  getArgsValues,
};
