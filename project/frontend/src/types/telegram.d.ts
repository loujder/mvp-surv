declare global {
  interface Window {
    Telegram?: {
      WebApp: {
        ready(): void;
        expand(): void;
        initData: string;
        initDataUnsafe: {
          user?: {
            id: number;
            first_name: string;
            last_name?: string;
            username?: string;
            language_code?: string;
          };
          chat_instance?: string;
          chat_type?: string;
          start_param?: string;
        };
      };
    };
  }
}

export {}; 