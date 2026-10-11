// adds dom matchers like toBeInTheDocument and toBeDisabled to expect
import '@testing-library/jest-dom';

// the jsdom build cra pins predates TextEncoder and TextDecoder, which react-router needs
import { TextEncoder, TextDecoder } from 'util';

if (typeof global.TextEncoder === 'undefined') {
  global.TextEncoder = TextEncoder;
}
if (typeof global.TextDecoder === 'undefined') {
  // node's decoder accepts a narrower input type than the dom one, but behaves the same here
  global.TextDecoder = TextDecoder as typeof global.TextDecoder;
}
