// Simple notification utility to replace react-hot-toast
export const toast = {
  success: (message: string) => {
    console.log(`SUCCESS: ${message}`);
    // In a real implementation, you could use native browser notifications
    // or implement a custom toast component
    alert(`Success: ${message}`);
  },
  error: (message: string) => {
    console.error(`ERROR: ${message}`);
    alert(`Error: ${message}`);
  },
  info: (message: string) => {
    console.info(`INFO: ${message}`);
    alert(`Info: ${message}`);
  }
};