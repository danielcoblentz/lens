import { render, screen } from "@testing-library/react";
import App from "./App";

// react-pdf ships as ESM, which jest cannot parse in CJS. The viewer is not
// what these routing tests are about.
jest.mock("./components/FileViewer", () => () => <div data-testid="file-viewer" />);

jest.mock("./services/aws");

test("renders the sidebar on the home route", () => {
  render(<App />);

  expect(screen.getByRole("heading", { name: "Lens" })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Files" })).toBeInTheDocument();
});

test("renders the document viewer on the home route", () => {
  render(<App />);

  expect(screen.getByTestId("file-viewer")).toBeInTheDocument();
});

test("renders the chat disabled until a document is selected", () => {
  render(<App />);

  expect(screen.getByPlaceholderText("Select a document first")).toBeDisabled();
  expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
});

test("starts with no files listed", () => {
  render(<App />);

  expect(screen.getByRole("button", { name: "Send" })).toBeInTheDocument();
  expect(screen.queryByText(/\.pdf$/)).not.toBeInTheDocument();
});
