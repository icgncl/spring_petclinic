import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    stages: [
        { duration: '30s', target: 1000 }, 
        { duration: '1m', target: 3000 },  
        { duration: '5m', target: 10000 }, 
        { duration: '1m', target: 0}
    ],
    thresholds: {
        http_req_duration: ['p(95)<200']
    }
};


const urls = [
    'http://gorilla-clinic-alb-1748401661.eu-west-1.elb.amazonaws.com',
    'http://gorilla-clinic-alb-1163147722.eu-west-2.elb.amazonaws.com'
];

export default function () {
    const index = __ITER % urls.length;
    const url = urls[index];

    const res = http.get(url);

    check(res, {
        'status is 200': (r) => r.status === 200,
        'response time < 200ms': (r) => r.timings.duration < 200,
    });

    sleep(1);
}
