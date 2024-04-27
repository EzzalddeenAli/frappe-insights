import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import frappeui from 'frappe-ui/vite'
import path from 'path'
import {defineConfig} from 'vite'
import {webserver_port} from '../../../sites/common_site_config.json'
import {viteExternalsPlugin} from 'vite-plugin-externals'
import { defineConfig } from 'vite'

export default defineConfig({
	plugins: [

		frappeui(), vue(), vueJsx(),
		// 	viteExternalsPlugin({
		//    vue: 'Vue',
		// // react: 'React',
		// // 'react-dom': 'ReactDOM',
		// // // value support chain, transform to window['React']['lazy']
		// // lazy: ['React', 'lazy']
		//  }),
	],
	esbuild: {loader: 'tsx'},
	resolve: {
		alias: {
			'@': path.resolve(__dirname, 'src'),
		},
	},
	build: {
		outDir: `../public/cdnLocal/apps/report-viewer`,
		emptyOutDir: true,
		target: 'es2015',
		// byEzz
	    // minify : false,
		outDir: `../insights/public/frontend`,
		emptyOutDir: true,
		target: 'es2015',
		sourcemap: true,
		rollupOptions: {
			//byEzz
			// external: ['vue'],

			output: {
				manualChunks: {
					'frappe-ui': ['frappe-ui'],
				},
			},
			//byEzz
			// globals: {
			// 	vue: 'Vue',
			// },
		},
	},
	optimizeDeps: {
		include: ['feather-icons', 'showdown', 'engine.io-client'],
	},
	define: {
		// enable hydration mismatch details in production build
		__VUE_PROD_HYDRATION_MISMATCH_DETAILS__: 'true',
	},
})
